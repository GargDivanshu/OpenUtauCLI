using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.IO.Compression;
using System.Linq;
using OpenUtau.App.ViewModels;
using OpenUtau.Core;
using OpenUtau.Classic;
using OpenUtau.Core.Util;
using OpenUtau.Core.Ustx;
using OpenUtau.Api;
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

                case "--track":
                    if (args.Length > 1 && args[1].ToLower() == "--add") {
                        HandleAddTrack();
                    } else if (args.Length > 1 && args[1].ToLower() == "--list") {
                        HandleListTracks(); // New method to list tracks
                    } else {
                        Console.WriteLine("Error: The --track command requires a valid subcommand.");
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
            Console.WriteLine($"Data path = {PathManager.Inst.DataPath}");
            Console.WriteLine($"Cache path = {PathManager.Inst.CachePath}");
            ToolsManager.Inst.Initialize();
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

        static void HandleListTracks() {
            try {
                var project = DocManager.Inst.Project;

                if (project == null) {
                    Console.WriteLine("No project is currently loaded.");
                    return;
                }

                Console.WriteLine($"Project: {project.name} (FilePath: {project.FilePath})");
                Console.WriteLine($"Found {project.tracks.Count} track(s).");

                foreach (var track in project.tracks) {
                    Console.WriteLine("-------------------------------------------------");
                    Console.WriteLine($"Track Name: {track.TrackName}");
                    Console.WriteLine($"Track Number: {track.TrackNo + 1}");
                    Console.WriteLine($"Singer: {track.Singer?.LocalizedName ?? "None"}");
                    Console.WriteLine($"Phonemizer: {track.Phonemizer?.GetType().Name ?? "DefaultPhonemizer"}");
                    Console.WriteLine($"Renderer: {track.RendererSettings?.Renderer?.ToString() ?? "None"}");
                    Console.WriteLine($"Singer Path: {track.Singer?.Location ?? "None"}");
                    Console.WriteLine("-------------------------------------------------");
                }
            } catch (Exception ex) {
                Console.WriteLine($"Failed to list tracks: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }
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

        static void HandleAddTrack() {
            try {
                var project = DocManager.Inst.Project;

                if (project == null) {
                    Console.WriteLine("No project is currently loaded.");
                    return;
                }

                Console.WriteLine($"Adding a new track to the project: {project.name} ({project.FilePath})");

                // Step 1: List all available singers
                Console.WriteLine("Searching for all singers...");
                SingerManager.Inst.SearchAllSingers();
                var keys = SingerManager.Inst.SingerGroups.Keys.OrderBy(k => k);
                var allSingers = new List<USinger>();

                foreach (var key in keys) {
                    var singers = SingerManager.Inst.SingerGroups[key];
                    if (singers != null && singers.Count > 0) {
                        allSingers.AddRange(singers);
                    }
                }

                if (allSingers.Count == 0) {
                    Console.WriteLine("No singers available to add to the track.");
                    return;
                }

                // Step 2: Display singers and allow user selection
                Console.WriteLine("Available singers:");
                for (int i = 0; i < allSingers.Count; i++) {
                    Console.WriteLine($"{i + 1}. {allSingers[i].LocalizedName} ({allSingers[i].SingerType})");
                }

                Console.Write("Select a singer by number: ");
                int selection;
                while (!int.TryParse(Console.ReadLine(), out selection) || selection < 1 || selection > allSingers.Count) {
                    Console.Write("Invalid selection. Please enter a valid number: ");
                }

                var selectedSinger = allSingers[selection - 1];
                Console.WriteLine($"You selected: {selectedSinger.LocalizedName}");

                // Step 3: Create and add a new track to the project
                var newTrack = new UTrack($"Track {project.tracks.Count + 1}");

                // Add the track to the project's track list
                project.tracks.Add(newTrack);
                Console.WriteLine($"New track {newTrack.TrackName} added. Total tracks now: {project.tracks.Count}");

                // Log project state after adding the track
                Log.Information($"After adding the track: Tracks={project.tracks.Count}");

                DocManager.Inst.StartUndoGroup();

                // Set the singer for the track
                var singerCommand = new TrackChangeSingerCommand(project, newTrack, selectedSinger);
                DocManager.Inst.ExecuteCmd(singerCommand);
                Console.WriteLine($"Singer {selectedSinger.LocalizedName} added to the track.");

                // End undo group and trigger autosave
                DocManager.Inst.EndUndoGroup();
                DocManager.Inst.AutoSave(); // Force an autosave immediately

                // Log project state after autosave
                Console.WriteLine($"Project state saved. Total tracks in project after autosave: {project.tracks.Count}");
                Log.Information($"Project state saved. Total tracks: {project.tracks.Count}");

                Preferences.Save();

                Console.WriteLine($"Track added successfully to the project.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to add track: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }
        }











        static void AddSingerToTrack(USinger singer) {
            try {
                var project = DocManager.Inst.Project;
                if (project == null || project.tracks.Count == 0) {
                    Console.WriteLine("No tracks available to add the singer.");
                    return;
                }

                // For simplicity, we'll add the singer to the first track.
                var track = project.tracks[0];

                // Start an undo group for combined operations
                DocManager.Inst.StartUndoGroup();

                // Change the singer for the track
                var singerCommand = new TrackChangeSingerCommand(project, track, singer);
                DocManager.Inst.ExecuteCmd(singerCommand);
                Console.WriteLine($"Singer {singer.LocalizedName} added to the track.");

                // Change the phonemizer for the track if applicable
                Phonemizer? newPhonemizer = null;

                if (!string.IsNullOrEmpty(singer?.Id) &&
                    Preferences.Default.SingerPhonemizers.TryGetValue(singer.Id, out var phonemizerTypeName)) {
                    var factory = DocManager.Inst.PhonemizerFactories.FirstOrDefault(f => f.type.FullName == phonemizerTypeName);
                    newPhonemizer = factory?.Create();
                } else if (!string.IsNullOrEmpty(singer?.DefaultPhonemizer)) {
                    var factory = DocManager.Inst.PhonemizerFactories.FirstOrDefault(f => f.type.FullName == singer.DefaultPhonemizer);
                    newPhonemizer = factory?.Create();
                }

                if (newPhonemizer == null) {
                    var factory = DocManager.Inst.PhonemizerFactories.FirstOrDefault(f => f.type == typeof(DefaultPhonemizer));
                    newPhonemizer = factory?.Create();
                }

                if (newPhonemizer != null) {
                    var phonemizerCommand = new TrackChangePhonemizerCommand(project, track, newPhonemizer);
                    DocManager.Inst.ExecuteCmd(phonemizerCommand);
                    Console.WriteLine($"Phonemizer {newPhonemizer.GetType().Name} added to the track.");
                } else {
                    Console.WriteLine("No valid phonemizer found for the selected singer.");
                }

                // Renderer selection based on singer type
                if (singer?.SingerType != null) {
                    string[] supportedRenderers = OpenUtau.Core.Render.Renderers.GetSupportedRenderers(singer.SingerType);
                    if (supportedRenderers.Length > 0) {
                        var rendererName = supportedRenderers[0]; // Select the first available renderer
                        var settings = new URenderSettings {
                            renderer = rendererName,
                        };
                        var rendererCommand = new TrackChangeRenderSettingCommand(project, track, settings);
                        DocManager.Inst.ExecuteCmd(rendererCommand);
                        Console.WriteLine($"Renderer {rendererName} added to the track.");
                    } else {
                        Console.WriteLine("No supported renderer found for the selected singer.");
                    }
                } else {
                    Console.WriteLine("Singer type is null, cannot determine renderer.");
                }

                // End the undo group
                DocManager.Inst.EndUndoGroup();

                // Notify for UI updates
                if (!string.IsNullOrEmpty(singer?.Id) && singer.Found) {
                    Preferences.Default.RecentSingers.Remove(singer.Id);
                    Preferences.Default.RecentSingers.Insert(0, singer.Id);
                    if (Preferences.Default.RecentSingers.Count > 16) {
                        Preferences.Default.RecentSingers.RemoveRange(
                            16, Preferences.Default.RecentSingers.Count - 16);
                    }
                }
                Preferences.Save();

                Console.WriteLine($"Singer, phonemizer, and renderer updated successfully for the track.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to add singer to track: {ex.Message}");
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
