using System;
using System.Collections.Generic;
using OpenAI.Chat;

string apiKey = Environment.GetEnvironmentVariable("OPENAI_TOKEN");

if (string.IsNullOrEmpty(apiKey))
{
    Console.WriteLine("Error: Please set your OPENAI_TOKEN environment variable.");
    return;
}

// Initialize the chat client using the gpt-4o model.
ChatClient client = new ChatClient(model: "gpt-4o", apiKey: apiKey);

// Start the conversation with a system prompt.
List<ChatMessage> messages = new List<ChatMessage>
    {
        new SystemChatMessage("You are a coding assistant to a developer at Open Dental. You will answer questions the developer may have about the API. Only answer with information based on the documentation you have access to.")
    };

Console.WriteLine("Documentation assistant started...");

while (true)
{
    // Read user input.
    Console.Write("User: ");
    string userInput = Console.ReadLine();

    // Add the user input to the conversation history.
    messages.Add(new UserChatMessage(userInput));
    ChatCompletion completion = client.CompleteChat(messages);

    if (completion != null && completion.Content.Count > 0)
    {
        // Retrieve and display the assistant's reply.
        string assistantReply = completion.Content[0].Text;
        Console.WriteLine("Assistant: " + assistantReply);

        // Append the assistant's reply into conversation history.
        messages.Add(new AssistantChatMessage(assistantReply));
    } else
    {
        Console.WriteLine("Error: Unable to get a response from the assistant.");
    }
}
