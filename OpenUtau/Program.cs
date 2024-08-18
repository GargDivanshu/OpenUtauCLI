using System;
using System.IO;

class Program {
    static void Main() {
        string path = @"C:\Users\divan\OneDrive\Desktop\AEOS\CLI_testing\OpenUtau\bin\Debug\net6.0-windows\Singers\Monone_v110";
        try {
            if (Directory.Exists(path)) {
                Console.WriteLine("Directory exists.");
                var files = Directory.GetFiles(path);
                Console.WriteLine("Files in directory:");
                foreach (var file in files) {
                    Console.WriteLine(file);
                }
            } else {
                Console.WriteLine("Directory does not exist.");
            }
        } catch (Exception ex) {
            Console.WriteLine($"Failed to access directory: {ex.Message}");
        }
    }
}
