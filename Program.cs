using System;
using ChatPOC.Chatbot;

namespace ChatPOC
{
    class Program
    {
        static void Main(string[] args)
        {
            try
            {
                var bot = new ChatPOC.Chatbot.Chatbot();
                bot.Run();
            } 
            catch (Exception ex)
            {
                Console.WriteLine($"FATAL ERROR: {ex.Message}");
            }
        }
    }
}