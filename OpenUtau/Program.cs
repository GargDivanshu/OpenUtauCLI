using System;
using System.IO;
using OpenUtau.Core.Util;
using System.Globalization;
using OpenUtau.App.ViewModels;
using OpenUtau.Core.Vogen;
using OpenUtau.Core;
using Serilog;

namespace OpenUtauCLI {
    class Program {
        static void Main(string[] args) {
            if (args.Length == 0) {
                ShowHelp();
                return;
            }

            InitializeCoreComponents();

            string command = args[0].ToLower();

            switch (command) {
                case "--init":
                    HandleInit();
                    break;

                case "--singer":
                    if (args.Length > 1) {
                        HandleSinger(args[1]);
                    } else {
                        Console.WriteLine("Error: The --singer command requires a singer path as an argument.");
                    }
                    break;

                case "--exit":
                    HandleExit();
                    break;

                default:
                    Console.WriteLine($"Error: Unknown command '{command}'.");
                    ShowHelp();
                    break;
            }
        }

        static void InitializeCoreComponents() {
            // Equivalent to InitCulture from App.axaml.cs
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;

            // Equivalent to InitOpenUtau from App.axaml.cs
            // PathManager.Inst.Initialize();
            Log.Information($"Data path = {PathManager.Inst.DataPath}");
            Log.Information($"Cache path = {PathManager.Inst.CachePath}");

            DocManager.Inst.Initialize();
            SingerManager.Inst.Initialize();

            // Optionally skip InitTheme as it is UI-related
            // Equivalent to InitAudio from App.axaml.cs
            // PlaybackManager.Inst.Initialize();
        }

        static void HandleInit() {
            Console.WriteLine("OpenUtau CLI initialized.");
        }

        static void HandleSinger(string singerPath) {
            try {
                // Load the singer using VogenSingerLoader or VogenSingerInstaller
                if (singerPath.EndsWith(VogenSingerInstaller.FileExt)) {
                    VogenSingerInstaller.Install(singerPath);
                } else {
                    string? basePath = Path.GetDirectoryName(singerPath);
                    if (string.IsNullOrEmpty(basePath)) {
                        Console.WriteLine("Error: Invalid singer path provided.");
                        return;
                    }
                    var loader = new VogenSingerLoader(basePath);
                    var singerObject = loader.LoadSinger(singerPath);
                    // Assuming that we want to add this singer to SingerManager
                    SingerManager.Inst.Singers.Add(singerObject.Id, singerObject);
                    Console.WriteLine($"Singer {singerObject.Name} loaded successfully.");
                }
            } catch (Exception ex) {
                Console.WriteLine($"Failed to load singer: {ex.Message}");
            }
        }

        static void HandleExit() {
            Console.WriteLine("Exiting OpenUtau CLI...");
            // Perform any necessary cleanup before exiting
            Environment.Exit(0); // Exit the application with a success code
        }


        static void ShowHelp() {
            Console.WriteLine("Usage:");
            Console.WriteLine("  openutauCLI --init          Initializes the OpenUtau CLI.");
            Console.WriteLine("  openutauCLI --singer [path] Loads and sets the singer from the specified path.");
            Console.WriteLine("  openutauCLI --exit          Exits the OpenUtau CLI.");
        }
    }
}
