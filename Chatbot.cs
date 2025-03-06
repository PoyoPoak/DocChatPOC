using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using OpenAI.Chat;

namespace ChatPOC.Chatbot
{
    public class Chatbot
    {
        private readonly ChatClient _client;
        private readonly List<ChatMessage> _messages;
        private string _apiKey = Environment.GetEnvironmentVariable("OPENAI_TOKEN");

        private static readonly ChatTool getDocumentationContextTool = ChatTool.CreateFunctionTool(
            functionName: "GetDocumentationContext",
            functionDescription: "Retrieve documentation context based on the developer's query.",
            functionParameters: BinaryData.FromBytes("""
                {
                    "type": "object",
                    "properties": {
                        "userInput": {
                            "type": "string",
                            "description": "The developer's query."
                        }
                    },
                    "required": [ "userInput" ]
                }
                """u8.ToArray())
        );

        public Chatbot()
        {
            if (string.IsNullOrEmpty(_apiKey))
            {
                throw new InvalidOperationException("Error: Missing OPENAI_TOKEN environment variable.");
            }
            
            string openaiModel = Environment.GetEnvironmentVariable("OPENAI_MODEL");
            _client = new ChatClient(model: openaiModel, apiKey: _apiKey);

            // Start the conversation with a system prompt.
            _messages = new List<ChatMessage>
            {
                new SystemChatMessage("You are a coding assistant to a developer at Open Dental. You will answer questions the developer may have about the API. Only answer with information based on the documentation you have access to. Your responses will be output in a console so be sure to format your responses for easy reading. Your responses shouldn't be long paragraphs. Keep it conscise and technical. Show code when you can from referenced documents.")
            };
        }

        public void Run()
        {
            Console.WriteLine("Documentation assistant started...");

            while (true)
            {
                Console.ForegroundColor = ConsoleColor.Blue;
                Console.Write("User: \n");
                Console.ResetColor();

                string userInput = Console.ReadLine();

                if (string.IsNullOrWhiteSpace(userInput))
                {
                    continue; // Skip empty input
                }

                // Add the user input to the conversation history.
                _messages.Add(new UserChatMessage(userInput));

                var options = new ChatCompletionOptions()
                {
                    Tools = { getDocumentationContextTool }
                };

                bool requiresAction;
                do
                {
                    requiresAction = false;
                    ChatCompletion completion = _client.CompleteChat(_messages, options);

                    switch (completion.FinishReason)
                    {
                        // When the chat is finished
                        case ChatFinishReason.Stop:
                        {
                            // Add the assistant message to the conversation history.
                            string assistantReply = completion.Content[0].Text;
                            _messages.Add(new AssistantChatMessage(assistantReply));

                            Console.ForegroundColor = ConsoleColor.Yellow;
                            Console.WriteLine("Assistant:");
                            Console.ResetColor();

                            // Reply
                            PrintFormatted(assistantReply);

                            break;
                        }

                        // When the chat requires funct calls
                        case ChatFinishReason.ToolCalls:
                            {
                                // Add the assistant's message (which includes tool calls) to the chat history
                                _messages.Add(new AssistantChatMessage(completion));

                                // Run functions requested by the bot
                                foreach (ChatToolCall toolCall in completion.ToolCalls)
                                {
                                    switch (toolCall.FunctionName)
                                    {
                                        case "GetDocumentationContext":
                                            {
                                                // Parse the tool's function arguments.
                                                using JsonDocument argumentsJson = JsonDocument.Parse(toolCall.FunctionArguments);
                                                if (!argumentsJson.RootElement.TryGetProperty("userInput", out JsonElement userInputElement))
                                                {
                                                    throw new ArgumentNullException("userInput", "The userInput argument is required.");
                                                }
                                                string queryInput = userInputElement.GetString();

                                                // Call the function to get documentation context.
                                                string toolResult = GetDocumentationContext(queryInput);
                                                _messages.Add(new ToolChatMessage(toolCall.Id, toolResult));
                                                Debug.WriteLine($"Tool '{toolCall.FunctionName}' retrieved '{toolResult}'");
                                                break;
                                            }
                                        default:
                                            {
                                                throw new NotImplementedException($"Tool function '{toolCall.FunctionName}' is not implemented.");
                                            }
                                    }
                                }
                                requiresAction = true;
                                break;
                            }
                        default:
                            {
                                throw new NotImplementedException($"Finish reason '{completion.FinishReason}' is not implemented.");
                            }
                    }
                } while (requiresAction);
            }
        }

        private void PrintFormatted(string text)
        {
            // Split the text on triple backticks and remove the newline
            string[] segments = Regex.Split(text, @"```").Select((x, i) => i % 2 == 0 ? x.Replace("\n", "") : x).ToArray();

            ConsoleColor defaultColor = Console.ForegroundColor;

            for (int i = 0; i < segments.Length; i++)
            {
                if (i % 2 == 1)
                {
                    // Color the code 
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine(segments[i]);
                    Console.ForegroundColor = defaultColor;
                } else
                {
                    Console.WriteLine(segments[i]);
                }
            }
        }

        private string ExtractQuery(string userInput)
        {
            // Send query through chatbot again as a reasoning agent to extract technical queries
            string openaiModel = Environment.GetEnvironmentVariable("OPENAI_MODEL");
            ChatClient extractor = new ChatClient(model: openaiModel, apiKey: _apiKey);
            List<ChatMessage> messages = new List<ChatMessage>
            {
                new SystemChatMessage("You are a reasoning agent that will extract technical queries from the user input. Only output a single query. This query will be used to query an information retrieval system. Keep it condensed and accurate to the input. For example if the user asks: How do I make an API call to get all the patient's benefits from their insurance plan? A proper extracted query would be: get patient benefits from insurance. Append the name of the documentation pages you referenced at the bottom of a response when you get context."),
                new UserChatMessage(userInput)
            };

            ChatCompletion extractedQuery = extractor.CompleteChat(messages);
            string query = extractedQuery.Content[0].Text.Trim();

            return query;
        }

        private List<string> RunQuery(string query)
        {
            string exeDirectory = AppContext.BaseDirectory;
            string workingDirectory = Environment.GetEnvironmentVariable("WORKING_DIR");

            if (!Directory.Exists(workingDirectory))
            {
                Console.WriteLine("Working directory does not exist: " + workingDirectory);
            }

            //Console.WriteLine(workingDirectory);

            ProcessStartInfo start = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"./query.py \"{query}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = workingDirectory
            };

            List<string> paths = new List<string>();

            using (Process process = Process.Start(start))
            {
                string output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                // Split the output into lines and trim whitespace
                string[] lines = output.Split(new[] { Environment.NewLine }, StringSplitOptions.RemoveEmptyEntries);

                // Append
                foreach (string line in lines)
                {
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        paths.Add(line.Trim());
                    }
                }
            }

            return paths;
        }

        private static string FetchContext(List<String> paths)
        {
            List<string> filesContents = new List<string>();

            foreach (string path in paths)
            {
                // Assume the returned path is relative if it isn't rooted.

                if (File.Exists(path))
                {
                    string fileContents = File.ReadAllText(path);
                    filesContents.Add(fileContents);
                } else
                {
                    Console.WriteLine($"File not found: {path}");
                }
            }

            // Combine all file contents into a single string.
            string context = string.Join("\n", filesContents);
            
            return context;
        }

        private string GetDocumentationContext(string userInput)
        {
            string query = ExtractQuery(userInput);
            List<string> paths = RunQuery(query);
            string context = FetchContext(paths);

            return context;
        }
    }
}