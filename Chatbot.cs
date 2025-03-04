using System;
using OpenAI.Chat;

namespace ChatPOC.Chatbot
{
    public class Chatbot
    {
        private readonly ChatClient _client;
        private readonly List<ChatMessage> _messages;

        public Chatbot()
        {
            string apiKey = Environment.GetEnvironmentVariable("OPENAI_TOKEN");
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
                Console.Write("User: ");
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
                    // Retrieve and display the assistant's reply.
                    string assistantReply = completion.Content[0].Text;
                    Console.WriteLine("Assistant: " + assistantReply);

                    // Append the assistant's reply to the conversation history.
                    _messages.Add(new AssistantChatMessage(assistantReply));
                } else
                {
                    Console.WriteLine("Error: Unable to get a response from the assistant.");
                }
            }
        }
    }
}
