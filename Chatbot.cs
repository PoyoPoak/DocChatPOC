using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using OpenAI.Chat;

namespace ChatPOC.Chatbot
{
    public class Chatbot
    {
        private readonly ChatClient _client;
        private readonly List<ChatMessage> _messages;
        private string apiKey = Environment.GetEnvironmentVariable("OPENAI_TOKEN");

        public Chatbot()
        {
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new InvalidOperationException("Error: Missing OPENAI_TOKEN environment variable.");
            }

            // Initialize the chat client using the gpt-4o model.
            _client = new ChatClient(model: "gpt-4o", apiKey: apiKey);

            // Start the conversation with a system prompt.
            _messages = new List<ChatMessage>
            {
                new SystemChatMessage("You are a coding assistant to a developer at Open Dental. You will answer questions the developer may have about the API. Only answer with information based on the documentation you have access to.")
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
                ChatCompletion completion = _client.CompleteChat(_messages);

                if (completion != null && completion.Content.Count > 0)
                {
                    string assistantReply = completion.Content[0].Text;

                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("Assistant:");
                    Console.ResetColor();

                    // Print formatted output with color
                    PrintFormatted(assistantReply);

                    // Append the assistant's reply to the conversation history.
                    _messages.Add(new AssistantChatMessage(assistantReply));
                }
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
            ChatClient extractor = new ChatClient(model: "gpt-4o", apiKey: apiKey);
            List<ChatMessage> messages = new List<ChatMessage>
            {
                new SystemChatMessage("You are a reasoning agent that will extract technical queries from the user input. Only output a single query. This query will be used to query an information retrieval system. Keep it condensed and accurate to the input. For example if the user asks: How do I make an API call to get all the patient's benefits from their insurance plan? A proper extracted query would be: get patient benefits from insurance"),
                new UserChatMessage(userInput)
            };

            ChatCompletion extractedQuery = extractor.CompleteChat();
            string query = extractedQuery.Content[0].Text;

            return query;
        }

        private List<string> RunQuery(string query)
        {

            // Run python with command "python3 query.py <query>" which will return 3 lines of output, each a path to a file
            ProcessStartInfo start = new ProcessStartInfo
            {
                FileName = "python3",
                Arguments = $"query.py {query}",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
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
            List<String> filesContents = new List<String>();

            // For each path, navigate through directory and fetch file contents from directory
            foreach (string path in paths)
            {
                if (File.Exists(path))
                {
                    string fileContents = File.ReadAllText(path);
                    filesContents.Add(fileContents);
                }
            }

            // Combine all file contents into a single string to return
            string context = string.Join("\n", filesContents);
            return context;
        }
    }
}