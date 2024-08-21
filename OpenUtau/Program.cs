using System;
using System.Globalization;
using System.IO;
using System.Linq;
using OpenUtau.App.ViewModels;
using OpenUtau.Core;
using OpenUtau.Core.Util;
using OpenUtau.Core.Vogen;
using OpenUtau.Core.DiffSinger;
using Serilog;
using OpenUtau.Classic;

namespace OpenUtauCLI {
    class Program {
        static void Main(string[] args) {
            if (args.Length == 0) {
                ShowHelp();
                return;
            }

            /*InitializeCoreComponents();*/

            string command = args[0].ToLower();

            switch (command) {
                case "--init":
                    HandleInit();
                    break;

                case "--singer":
                    if (args.Length > 2) {
                        HandleSinger(args[1], args[2]);
                    } else {
                        Console.WriteLine("Error: The --singer command requires a format and a singer path as arguments.");
                    }
                    break;

                case "--install_singer":
                    if (args.Length > 2) {
                        HandleInstallSinger(args[1], args[2]);
                    } else {
                        Console.WriteLine("Error: The --install_singer command requires a format and a path to a singer file.");
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
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;
            InitLogging();
            Log.Information($"Data path = {PathManager.Inst.DataPath}");
            Log.Information($"Cache path = {PathManager.Inst.CachePath}");
            DocManager.Inst.Initialize();
            SingerManager.Inst.Initialize();
            InitAudio();
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
                Log.Information("Audio initialized.");
            } catch (Exception ex) {
                Log.Error(ex, "Failed to initialize audio.");
            }
        }

        static void HandleInit() {
            Console.WriteLine("OpenUtau CLI initialized.");
            InitializeCoreComponents();
        }

        static void HandleInstallSinger(string format, string singerFilePath) {
            try {
                Console.WriteLine($"Attempting to install singer from: {singerFilePath}");

                // Ensure that the SingersPath is created
                Directory.CreateDirectory(PathManager.Inst.SingersPath);

                if (format == "--vogen" && singerFilePath.EndsWith(VogenSingerInstaller.FileExt)) {
                    Console.WriteLine("Recognized Vogen singer installer file.");
                    VogenSingerInstaller.Install(singerFilePath);
                } else if (format == "--diffsinger" && singerFilePath.EndsWith(".zip")) {
                    var extractPath = Path.Combine(PathManager.Inst.SingersPath, Path.GetFileNameWithoutExtension(singerFilePath));

                    // Clean up the target directory if it already exists
                    if (Directory.Exists(extractPath)) {
                        Console.WriteLine($"Cleaning up existing directory: {extractPath}");
                        Directory.Delete(extractPath, true); // Delete the directory and its contents
                    }

                    // Extract the singer files
                    System.IO.Compression.ZipFile.ExtractToDirectory(singerFilePath, extractPath);
                    HandleSinger("--diffsinger", extractPath); // Pass the extracted directory to HandleSinger
                } else {
                    Console.WriteLine($"Unsupported file type or format for singer installation: {format}");
                }

                Console.WriteLine("Singer installation process completed.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to install singer from: {singerFilePath}");
                Console.WriteLine($"Error: {ex.Message}");
            }
        }

        static void HandleSinger(string format, string singerPath) {
            try {
                string basePath = Path.GetDirectoryName(singerPath) ?? singerPath;

                Console.WriteLine($"Attempting to load singer from: {singerPath}");

                if (format == "--vogen") {
                    var loader = new VogenSingerLoader(basePath);
                    var singerObject = loader.LoadSinger(singerPath);
                    SingerManager.Inst.Singers.Add(singerObject.Id, singerObject);
                    Console.WriteLine($"Singer {singerObject.Name} loaded successfully.");
                } else if (format == "--diffsinger") {
                    // Use VoicebankLoader to load the voicebank
                    Console.WriteLine("Recognized DiffSinger voicebank.");
                    var loader = new VoicebankLoader(basePath);
                    var voicebanks = loader.SearchAll();

                    bool foundDiffSinger = false;
                    foreach (var voicebank in voicebanks) {
                        Console.WriteLine($"Loading voicebank: {voicebank.Name}");
                        if (voicebank.SingerType == OpenUtau.Core.Ustx.USingerType.DiffSinger) {
                            var singer = new DiffSingerSinger(voicebank);
                            SingerManager.Inst.Singers.Add(singer.Id, singer);
                            Console.WriteLine($"DiffSinger {singer.Id} loaded successfully.");
                            foundDiffSinger = true;
                        }
                    }

                    if (!foundDiffSinger) {
                        Console.WriteLine("No DiffSinger voicebank found.");
                    }
                } else {
                    Console.WriteLine("Error: Unsupported format. Use --vogen or --diffsinger.");
                }

                // Find all singers and log them
                var singers = ClassicSingerLoader.FindAllSingers();
                if (singers.Any()) {
                    Console.WriteLine("Available singers after loading:");
                    foreach (var singer in singers) {
                        Console.WriteLine("-------------------------------------------------");
                        Console.WriteLine($"Singer Name: {singer.Name}");
                        Console.WriteLine($"Singer ID: {singer.Id}");
                        Console.WriteLine($"Singer Type: {singer.SingerType}");
                        Console.WriteLine($"Singer Author: {singer.Author}");
                        Console.WriteLine($"Singer Voice: {singer.Voice}");
                        Console.WriteLine($"Singer Web: {singer.Web}");
                        Console.WriteLine($"Singer Version: {singer.Version}");
                        Console.WriteLine($"Singer Base Path: {singer.BasePath}");
                        Console.WriteLine("-------------------------------------------------");
                    }
                } else {
                    Console.WriteLine("No singers found.");
                }
            } catch (UnauthorizedAccessException uae) {
                Console.WriteLine($"Access denied: {uae.Message}");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to load singer: {ex.Message}");
            }
        }



        static void HandleExit() {
            Console.WriteLine("Exiting OpenUtau CLI...");
            Environment.Exit(0);
        }

        static void ShowHelp() {
            Console.WriteLine("Usage:");
            Console.WriteLine("  openutauCLI --init          Initializes the OpenUtau CLI.");
            Console.WriteLine("  openutauCLI --singer [format] [path] Loads and sets the singer from the specified path in the specified format.");
            Console.WriteLine("  openutauCLI --install_singer [format] [path] Installs a singer from the specified path in the specified format.");
            Console.WriteLine("  openutauCLI --exit          Exits the OpenUtau CLI.");
        }
    }
}
