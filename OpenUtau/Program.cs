using System;
using System.Globalization;
using System.IO;
using OpenUtau.App.ViewModels;
using OpenUtau.Core;
using OpenUtau.Core.Util;
using OpenUtau.Core.Vogen;
using Serilog;
using System.Security.AccessControl;
using System.Security.Principal;


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

            // Log initialization details
            InitLogging();

            // Equivalent to InitOpenUtau from App.axaml.cs
            Log.Information($"Data path = {PathManager.Inst.DataPath}");
            Log.Information($"Cache path = {PathManager.Inst.CachePath}");

            DocManager.Inst.Initialize();
            SingerManager.Inst.Initialize();

            // Optionally skip InitTheme as it is UI-related
            InitAudio(); // Initialize audio if necessary
        }

        static void InitLogging() {
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .WriteTo.Debug()
                .WriteTo.Logger(lc => lc
                    .MinimumLevel.Information()
                    .WriteTo.File(PathManager.Inst.LogFilePath, rollingInterval: RollingInterval.Day, encoding: System.Text.Encoding.UTF8))
                .WriteTo.Logger(lc => lc
                    .MinimumLevel.ControlledBy(DebugViewModel.Sink.Inst.LevelSwitch)
                    .WriteTo.Sink(DebugViewModel.Sink.Inst))
                .CreateLogger();
            AppDomain.CurrentDomain.UnhandledException += (sender, args) => {
                Log.Error((Exception)args.ExceptionObject, "Unhandled exception");
            };
            Log.Information("Logging initialized.");
        }

        static void InitAudio() {
            try {
                // PlaybackManager.Inst.Initialize();
                Log.Information("Audio initialized.");
            } catch (Exception ex) {
                Log.Error(ex, "Failed to initialize audio.");
            }
        }

        static void HandleInit() {
            Console.WriteLine("OpenUtau CLI initialized.");
        }

        static void HandleSinger(string singerPath) {
            try {
                string? basePath = Path.GetDirectoryName(singerPath);
                if (string.IsNullOrEmpty(basePath)) {
                    Console.WriteLine("Error: Invalid singer path provided.");
                    return;
                }

                // Test file access explicitly
                Console.WriteLine("Testing file access...");
                var testFiles = Directory.GetFiles(basePath);
                foreach (var file in testFiles) {
                    Console.WriteLine($"Attempting to read file: {file}");
                    try {
                        File.ReadAllText(file);
                        Console.WriteLine($"File read successfully: {file}");
                    } catch (Exception ex) {
                        Console.WriteLine($"Failed to read file: {file}, Error: {ex.Message}");
                    }
                }

                // Detailed logging before loading singer
                Console.WriteLine($"Attempting to load singer from: {singerPath}");
                var loader = new VogenSingerLoader(basePath);
                var singerObject = loader.LoadSinger(singerPath);
                SingerManager.Inst.Singers.Add(singerObject.Id, singerObject);
                Console.WriteLine($"Singer {singerObject.Name} loaded successfully.");
            } catch (UnauthorizedAccessException uae) {
                Console.WriteLine($"Access denied: {uae.Message}");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to load singer: {ex.Message}");
            }
        }



        static bool HasReadPermissionOnDir(string path) {
            try {
                // Attempt to get the directory's files as a quick test for read access.
                var files = Directory.GetFiles(path);
                return true;
            } catch (UnauthorizedAccessException) {
                return false;
            } catch (Exception) {
                return false;
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
