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

        private static UProject? project;

        static void Main(string[] args) {
            Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);

            if (args.Length == 0) {
                ShowHelp();
                return;
            }

            InitializeCoreComponents();

            while (true) {
                Console.Write("> ");
                string input = Console.ReadLine()?.Trim() ?? string.Empty;
                if (string.IsNullOrEmpty(input)) continue;

                string[] parts = input.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                string command = parts[0].ToLower();

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
                        if (parts.Length > 1) {
                            switch (parts[1].ToLower()) {
                                case "--add":
                                    HandleAddTrack();
                                    break;
                                case "--list":
                                    HandleListTracks();
                                    break;
                                case "--update":
                                    HandleUpdateTrack();
                                    break;
                                default:
                                    Console.WriteLine("Invalid subcommand for '--track'.");
                                    break;
                            }
                        } else {
                            Console.WriteLine("Error: The '--track' command requires a valid subcommand.");
                        }
                        break;

                    case "--part":
                        if (parts.Length > 1) {
                            switch (parts[1].ToLower()) {
                                case "--add":
                                    HandleAddPart();
                                    break;
                                case "--delete":
                                    HandleDeletePart();
                                    break;
                                case "--rename":
                                    HandleRenamePart();
                                    break;
                                case "--list":
                                    HandleListParts();
                                    break;
                                default:
                                    Console.WriteLine("Invalid subcommand for '--part'.");
                                    break;
                            }
                        } else {
                            Console.WriteLine("Error: The '--part' command requires a valid subcommand.");
                        }
                        break;


                    case "--import":
                        if (parts.Length > 1) {
                            switch (parts[1].ToLower()) {
                                case "--midi":
                                    if (parts.Length > 2 && parts[1].ToLower() == "--midi") {
                                        string filePath = parts[2];
                                        HandleImportMidi(filePath);
                                    } else {
                                        Console.WriteLine("Error: Please specify the MIDI file path.");
                                    }
                                    break;
                                default:
                                    Console.WriteLine("Invalid subcommand for '--import'.");
                                    break;
                            }
                        } else {
                            Console.WriteLine("Error: The '--import' command requires a subcommand.");
                        }
                        break;

                    /*case "--process":
                        if (parts.Length > 1) {
                            switch (parts[1].ToLower()) {
                                case "--loadRenderedPitch":
                                    HandleLoadRenderedPitch();
                                    break;
                                default:
                                    Console.WriteLine("Invalid subcommand for '--process'.");
                                    break;
                            }
                        } else {
                            Console.WriteLine("Error: The '--process' command requires a valid subcommand.");
                        }
                        break;*/



                    case "--exit":
                        HandleExit();
                        break;

                    default:
                        Console.WriteLine($"Error: Unknown command '{command}'.");
                        ShowHelp();
                        break;
                }
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
            if (project == null) {
                DocManager.Inst.Initialize(); // Only initialize if project is not already set
                project = DocManager.Inst.Project; // Assign the project instance
            }
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
            if (project == null) {
                InitializeCoreComponents(); // Ensures components are initialized if not already
            } else {
                Console.WriteLine("Project already initialized.");
            }
        }

        static void HandleListTracks() {
            try {
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


        static void HandleUpdateTrack() {
            if (project == null || project.tracks.Count == 0) {
                Console.WriteLine("No project or tracks loaded. Cannot update a track.");
                return;
            }

            // List existing tracks for user selection
            Console.WriteLine("Select a track to update:");
            for (int i = 0; i < project.tracks.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.tracks[i].TrackName}");
            }

            Console.Write("Choose track number: ");
            if (!int.TryParse(Console.ReadLine(), out int trackIndex) || trackIndex < 1 || trackIndex > project.tracks.Count) {
                Console.WriteLine("Invalid track number.");
                return;
            }

            UTrack selectedTrack = project.tracks[trackIndex - 1];
            Console.WriteLine($"You selected: {selectedTrack.TrackName}");

            // List available singers
            SingerManager.Inst.SearchAllSingers();
            var allSingers = SingerManager.Inst.SingerGroups.SelectMany(g => g.Value).ToList();
            if (allSingers.Count == 0) {
                Console.WriteLine("No singers available to update the track.");
                return;
            }

            Console.WriteLine("Available singers:");
            for (int i = 0; i < allSingers.Count; i++) {
                Console.WriteLine($"{i + 1}. {allSingers[i].LocalizedName} ({allSingers[i].SingerType})");
            }

            Console.Write("Select a singer by number: ");
            if (!int.TryParse(Console.ReadLine(), out int singerIndex) || singerIndex < 1 || singerIndex > allSingers.Count) {
                Console.WriteLine("Invalid singer selection.");
                return;
            }

            USinger selectedSinger = allSingers[singerIndex - 1];
            Console.WriteLine($"You selected: {selectedSinger.LocalizedName}");

            // Update track with new singer
            DocManager.Inst.StartUndoGroup();
            var singerCommand = new TrackChangeSingerCommand(project, selectedTrack, selectedSinger);
            DocManager.Inst.ExecuteCmd(singerCommand);
            Console.WriteLine($"Updated singer of track '{selectedTrack.TrackName}' to '{selectedSinger.LocalizedName}'.");

            // You can extend this to update phonemizer and renderer here if needed

            DocManager.Inst.EndUndoGroup();
            DocManager.Inst.AutoSave();
            Console.WriteLine("Track updated and project state saved.");
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

                Preferences.Save();

                Console.WriteLine($"Track added successfully to the project.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to add track: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }
        }



        static void HandleListParts() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project loaded or no parts available.");
                return;
            }

            Console.WriteLine("Listing all parts:");
            foreach (var part in project.parts) {
                Console.WriteLine($"Part Name: {part.name}, Track: {part.trackNo + 1}, Position: {part.position}, Duration: {part.Duration}");
            }
        }



        static void HandleAddPart() {
            if (project == null || project.tracks.Count == 0) {
                Console.WriteLine("No project or tracks loaded. Cannot add a part.");
                return;
            }

            Console.WriteLine("Select a track to add the part:");
            for (int i = 0; i < project.tracks.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.tracks[i].TrackName}");
            }

            Console.Write("Choose track number: ");
            if (!int.TryParse(Console.ReadLine(), out int trackIndex) || trackIndex < 1 || trackIndex > project.tracks.Count) {
                Console.WriteLine("Invalid track number.");
                return;
            }

            // Create a new voice part in the selected track
            UVoicePart newPart = new UVoicePart {
                trackNo = trackIndex - 1, // Track index adjustment for zero-based index
                name = "New Part",
                position = 0,
                duration = 480 // Default duration, modify as necessary
            };

            // Execute the AddPartCommand
            AddPartCommand addPartCommand = new AddPartCommand(project, newPart);
            addPartCommand.Execute();
            Console.WriteLine($"Added new part to track {trackIndex}: {newPart.name}");
        }


        static void HandleDeletePart() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project or parts loaded. Cannot delete a part.");
                return;
            }

            // List parts for user to choose
            Console.WriteLine("Select a part to delete:");
            for (int i = 0; i < project.parts.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.parts[i].name} in track {project.parts[i].trackNo + 1}");
            }

            Console.Write("Choose part number: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            // Execute the RemovePartCommand
            UPart partToRemove = project.parts[partIndex - 1];
            RemovePartCommand removePartCommand = new RemovePartCommand(project, partToRemove);
            removePartCommand.Execute();
            Console.WriteLine($"Removed part: {partToRemove.name}");
        }

        static void HandleRenamePart() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project or parts loaded. Cannot rename a part.");
                return;
            }

            // List parts for user to choose
            Console.WriteLine("Select a part to rename:");
            for (int i = 0; i < project.parts.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.parts[i].name} in track {project.parts[i].trackNo + 1}");
            }

            Console.Write("Choose part number: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            Console.Write("Enter new name for the part: ");
            string newName = Console.ReadLine() ?? string.Empty; // Provide a default empty string if null

            if (string.IsNullOrWhiteSpace(newName)) {
                Console.WriteLine("Invalid part name.");
                return;
            }

            // Proceed with renaming the part using newName

            if (string.IsNullOrWhiteSpace(newName)) {
                Console.WriteLine("Invalid part name.");
                return;
            }

            // Execute the RenamePartCommand
            UPart partToRename = project.parts[partIndex - 1];
            RenamePartCommand renamePartCommand = new RenamePartCommand(project, partToRename, newName);
            renamePartCommand.Execute();
            Console.WriteLine($"Renamed part to: {newName}");
        }


        static void HandleImportMidi(string filePath) {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }

            filePath = filePath.Trim('"').Replace('/', Path.DirectorySeparatorChar);

            Console.WriteLine($"Received file path: {filePath}");  // Debug output

            if (string.IsNullOrWhiteSpace(filePath)) {
                Console.WriteLine("Invalid file path.");
                return;
            }

            if (!File.Exists(filePath)) {
                Console.WriteLine($"File does not exist at {filePath}."); // More detailed error message
                return;
            }

            try {
                var parts = OpenUtau.Core.Format.MidiWriter.Load(filePath, project);
                DocManager.Inst.StartUndoGroup();
                foreach (var part in parts) {
                    var track = new UTrack { TrackNo = project.tracks.Count };
                    part.trackNo = track.TrackNo;
                    if (part.name != "New Part") {
                        track.TrackName = part.name;
                    }
                    part.AfterLoad(project, track);
                    DocManager.Inst.ExecuteCmd(new AddTrackCommand(project, track));
                    DocManager.Inst.ExecuteCmd(new AddPartCommand(project, part));
                }
                DocManager.Inst.EndUndoGroup();
                Console.WriteLine("MIDI file imported successfully.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to import MIDI: {ex.Message}");
            }
        }



        /*static void HandleLoadRenderedPitch() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project or parts loaded.");
                return;
            }

            // List parts for user selection
            Console.WriteLine("Select a part to process:");
            for (int i = 0; i < project.parts.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.parts[i].name}");
            }

            // Get user input
            Console.Write("Choose part number: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            // Retrieve the selected part
            UPart selectedPart = project.parts[partIndex - 1];
            if (!(selectedPart is UVoicePart voicePart)) {
                Console.WriteLine("Selected part is not a voice part.");
                return;
            }

            // Assuming LoadRenderedPitch is a method that needs to be implemented or a class that needs to be instantiated and run
            LoadRenderedPitch pitchLoader = new LoadRenderedPitch();
            pitchLoader.Run(project, voicePart, new List<UNote>(), DocManager.Inst); // Adjust parameters as necessary

            Console.WriteLine("Rendered pitch loading completed for selected part.");
        }
*/






        /*static void AddSingerToTrack(USinger singer) {
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
        }*/







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
