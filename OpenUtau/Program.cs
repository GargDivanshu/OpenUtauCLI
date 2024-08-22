using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.IO.Compression;
using System.Linq;
using OpenUtau.App.ViewModels;
using OpenUtau.Core;
using OpenUtau.Classic;
using OpenUtau.Core.Util;
using OpenUtau.Core.Ustx;
using OpenUtau.Core.DiffSinger;
using Serilog;

namespace OpenUtauCLI {
    class Program {
        static void Main(string[] args) {
            Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

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

                case "--install_singer":
                    if (args.Length > 2) {
                        HandleInstallSinger(args[1], args[2]); // Ensure both format and path are provided
                    } else {
                        Console.WriteLine("Error: The --install_singer command requires a format and a path to a singer file.");
                    }
                    break;


                case "--singer":
                    HandleListSingers();
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
            Console.WriteLine($"Data path = {PathManager.Inst.DataPath}");
            Console.WriteLine($"Cache path = {PathManager.Inst.CachePath}");
            DocManager.Inst.Initialize();
            SingerManager.Inst.Initialize();
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

        static void HandleInit() {
            Console.WriteLine("OpenUtau CLI initialized.");
            InitializeCoreComponents();
        }

        static void HandleInstallSinger(string format, string singerFilePath) {
            try {
                Console.WriteLine($"Attempting to install singer from: {singerFilePath}");

                // Determine the extraction path
                var extractPath = Path.Combine(PathManager.Inst.SingersPath, Path.GetFileNameWithoutExtension(singerFilePath));
                Console.WriteLine($"Extracted to: {extractPath}");

                // Clean up the target directory if it already exists
                if (Directory.Exists(extractPath)) {
                    Console.WriteLine($"Cleaning up existing directory: {extractPath}");
                    Directory.Delete(extractPath, true); // Delete the directory and its contents
                }

                // Extract the singer files
                System.IO.Compression.ZipFile.ExtractToDirectory(singerFilePath, extractPath);
                Console.WriteLine("Extraction completed.");

                // Recursively search for the dsconfig.yaml file
                var dsConfigFiles = Directory.GetFiles(extractPath, "dsconfig.yaml", SearchOption.AllDirectories);

                if (dsConfigFiles.Length == 0) {
                    Console.WriteLine("Error: dsconfig.yaml not found after extraction.");
                    return;
                }

                // Assuming there might be multiple dsconfig.yaml files, we'll handle the first one found
                var dsConfigPath = dsConfigFiles[0];
                Console.WriteLine($"Found dsconfig.yaml at: {dsConfigPath}");

                // Attempt to load the singer using the found dsconfig.yaml file
                HandleSinger("--diffsinger", dsConfigPath);

                Console.WriteLine("Singer installation process completed.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to install singer from: {singerFilePath}");
                Console.WriteLine($"Error: {ex.Message}");
            }
        }


        static void HandleSinger(string format, string dsConfigPath) {
            try {
                Console.WriteLine($"Attempting to load singer from: {dsConfigPath}");

                // Extract the base path from dsConfigPath
                string? basePath = Path.GetDirectoryName(dsConfigPath);
                if (basePath == null) {
                    Console.WriteLine("Error: Could not determine the base path from dsConfigPath.");
                    return;
                }

                // Create a Voicebank object
                var voicebank = new Voicebank() {
                    File = dsConfigPath,
                    BasePath = basePath
                };

                // Load the Voicebank data
                VoicebankLoader.LoadVoicebank(voicebank);

                // Create the appropriate singer based on the format
                USinger? singer = null;
                if (format == "--diffsinger") {
                    Console.WriteLine("Loading DiffSinger singer...");
                    singer = new DiffSingerSinger(voicebank);
                } else {
                    Console.WriteLine($"Error: Unsupported singer format {format}");
                    return;
                }

                if (singer == null) {
                    Console.WriteLine("Error: Failed to create a valid singer object.");
                    return;
                }

                // Add the singer to the SingerManager
                SingerManager.Inst.Singers[singer.Id] = singer;
                Console.WriteLine($"Singer {singer.Name} loaded successfully.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to load singer: {ex.Message}");
            }
        }






        static void HandleListSingers() {
            try {
                Console.WriteLine("Searching for all singers...");
                SingerManager.Inst.SearchAllSingers();

                // Retrieve the loaded singers from the SingerManager's SingerGroups
                var keys = SingerManager.Inst.SingerGroups.Keys.OrderBy(k => k);
                if (keys != null) {
                    Console.WriteLine($"Found {keys.Count()} singer group(s).");
                    foreach (var key in keys) {
                        Console.WriteLine($"Singer Group: {key}");
                        var singers = SingerManager.Inst.SingerGroups[key];
                        if (singers != null && singers.Count > 0) {
                            Console.WriteLine($"Found {singers.Count} singer(s) in group {key}.");
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
                            Console.WriteLine($"No singers found in group {key}.");
                        }
                    }
                } else {
                    Console.WriteLine("No singer groups found.");
                }
            } catch (Exception ex) {
                Console.WriteLine($"Failed to list singers: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }
        }




        static void HandleExit() {
            Console.WriteLine("Exiting OpenUtau CLI...");
            Environment.Exit(0);
        }

        static void ShowHelp() {
            Console.WriteLine("Usage:");
            Console.WriteLine("  openutauCLI --init          Initializes the OpenUtau CLI.");
            Console.WriteLine("  openutauCLI --install_singer [path] Installs a singer from the specified path.");
            Console.WriteLine("  openutauCLI --exit          Exits the OpenUtau CLI.");
        }
    }
}
