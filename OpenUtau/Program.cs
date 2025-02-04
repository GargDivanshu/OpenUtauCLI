using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.IO.Compression;
using System.Linq;
using OpenUtau.App.ViewModels;
using OpenUtau.Core;
using OpenUtau.Classic;
using OpenUtau.Core.Util;
using OpenUtau.Core.Ustx;
using OpenUtau.Core.Editing;
using OpenUtau.Api;
using OpenUtau.Audio;
using OpenUtau.Core.DiffSinger;
using Serilog;


namespace OpenUtauCLI {
    class Program {

        private static UProject? project;
        // private static MainWindowViewModel viewModel;

        static void Main(string[] args) {
            Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);


            if (args.Length == 0) {
                ShowHelp();
                return;
            }

            // if (args.Length > 1 && args[0] == "--pipeline") {
            //     Pipeline(args.Skip(1).ToArray());
            //     return; // Exit after handling the pipeline, no need for interactive loop
            // }

            //InitializeCoreComponents();
            

            while (true) {
                Console.Write("> ");
                string input = Console.ReadLine()?.Trim() ?? string.Empty;
                if (string.IsNullOrEmpty(input)) continue;

                string[] parts = input.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                string command = parts[0].ToLower();

                switch (command) {

                    // case "--pipeline":
                    //     if(parts.Length > 1) {
                    //         Pipeline(parts.Skip(1).ToArray());
                    //     } else {
                    //         Console.WriteLine("Error: '--pipeline' requires a series of subcommands for importing midi (--midi), adding lyrics (--lyrics), wav file path for exporting (--export)");
                    //     }
                        
                    //     break;


                    case "--init":
                        HandleInit();
                        break;

                    case "--install":
                        if (parts.Length > 1) {
                            switch (parts[1].ToLower()) {
                                case "--singer":
                                    if (parts.Length > 3) {
                                        HandleInstallSinger(parts[2], parts[3]); // Format and path are provided
                                    } else {
                                        Console.WriteLine("Error: The --install --singer command requires a format and a path to a singer file.");
                                    }
                                    break;
                                case "--dependency":
                                    if (parts.Length > 2) {
                                        HandleInstallDependency(parts[2]); // Path is provided
                                    } else {
                                        Console.WriteLine("Error: The --install --dependency command requires a path to a dependency file.");
                                    }
                                    break;
                                default:
                                    Console.WriteLine("Invalid subcommand for '--install'.");
                                    break;
                            }
                        } else {
                            Console.WriteLine("Error: The '--install' command requires a subcommand.");
                        }
                        break;

                    case "--info":
                        HandlePartInfo();
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
                                case "--remove":
                                    RemoveTrack();
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


                    case "--phonemizers":
                        ListPhonemizers();
                        break;

                    case "--phonemizers --update":
                        HandleUpdatePhonemizer();
                        break;


                    case "--export":
                        if (parts.Length > 1 && parts[1].ToLower() == "--wav") {
                            HandleExportWavCommand();
                        } else {
                            Console.WriteLine("Error: Specify the format to export (e.g., --export --wav).");
                        }
                        break;


                    case "--save":
                        HandleSaveCommand();
                        break;


                    case "--lyrics":
                        if (parts.Length > 1) {
                            HandleLyricsCommand(parts[1]);
                        } else {
                            Console.WriteLine("Error: Please specify the path to the lyrics file.");
                        }
                        break;


                    case "--process":
                        if (parts.Length > 1 && parts[1].ToLower() == "--pitch") {
                            HandleLoadRenderedPitch();
                        } else if (parts.Length > 1 && parts[1].ToLower() == "--transpose") {
                            HandleTranspose(Int32.Parse(parts[2]));
                        } else if (parts.Length > 1 && parts[1].ToLower() == "--bpm") {
                            ChangeBPM(Int32.Parse(parts[2]));
                        } else if (parts.Length > 1 && parts[1].ToLower() == "--vcolor") {
                            SetVoiceColor();
                        } else { 
                            Console.WriteLine("Invalid subcommand for '--process'.");
                        }
                        break;

                    case "--help":
                        // Check if there's a specific command to provide help for
                        string? helpCommand = parts?.Length > 1 ? parts[1] : null;
                        ShowHelp(helpCommand);
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
        }

        //static void InitializeCLIViewModel() {
        //    viewModel = new MainWindowViewModel();

        //    // Initialize singer and project
        //    TaskScheduler scheduler = TaskScheduler.Default;
        //    viewModel.GetInitSingerTask()!.ContinueWith(_ => {
        //        viewModel.InitProject();
        //        Console.WriteLine("Initialized CLI ViewModel with project and commands.");
        //    }, CancellationToken.None, TaskContinuationOptions.None, scheduler);

            
        //    project = DocManager.Inst.Project;
        //    // Set up autosave timer if necessary
        //    //var autosaveTimer = new Timer((e) => DocManager.Inst.AutoSave(), null, TimeSpan.Zero, TimeSpan.FromSeconds(30));
        //}

        // static async void Pipeline(string[] args) {
        //     string midiPath = "";
        //     string lyricsPath = "";
        //     string exportPath = "";

        //     // Parse the flags and their values
        //     for (int i = 0; i < args.Length; i++) {
        //         switch (args[i].ToLower()) {
        //             case "--midi":
        //                 if (i + 1 < args.Length) {
        //                     midiPath = args[i + 1]; // Capture MIDI path
        //                     i++; // Skip the next argument since it's the value
        //                 } else {
        //                     Console.WriteLine("Error: Missing value for --midi.");
        //                     return;
        //                 }
        //                 break;

        //             case "--lyrics":
        //                 if (i + 1 < args.Length) {
        //                     lyricsPath = args[i + 1]; // Capture lyrics string
        //                     i++;
        //                 } else {
        //                     Console.WriteLine("Error: Missing value for --lyrics.");
        //                     return;
        //                 }
        //                 break;

        //             case "--export":
        //                 if (i + 1 < args.Length) {
        //                     exportPath = args[i + 1]; // Capture export path
        //                     i++;
        //                 } else {
        //                     Console.WriteLine("Error: Missing value for --export.");
        //                     return;
        //                 }
        //                 break;

        //             default:
        //                 Console.WriteLine($"Error: Unknown argument {args[i]}.");
        //                 return;
        //         }
        //     }

        //     // Validate that all required arguments are provided
        //     if (string.IsNullOrEmpty(midiPath) || string.IsNullOrEmpty(lyricsPath) || string.IsNullOrEmpty(exportPath)) {
        //         Console.WriteLine("Error: Missing required arguments. Make sure to include --midi, --lyrics, and --export.");
        //         return;
        //     }

            
        //     // Initialize the core components before proceeding with the pipeline
        //     InitializeCoreComponentsViaPipeline();

        //     // Call the respective functions
        //     Console.WriteLine($"Importing MIDI from: {midiPath}");
        //     HandleImportMidi(midiPath);  // Assuming this method exists for importing MIDI

        //     ListTracks();
        //     int trackCount = DocManager.Inst.Project.tracks.Count;
        //     var trackToRemove = DocManager.Inst.Project.tracks[0];

        //     DocManager.Inst.StartUndoGroup();
        //     DocManager.Inst.ExecuteCmd(new RemoveTrackCommand(DocManager.Inst.Project, trackToRemove));
        //     DocManager.Inst.EndUndoGroup();

        //     Console.WriteLine($"Track '{trackToRemove.TrackName}' has been successfully removed.");
        //     ListTracks();

        //     // Applying lyrics
        //     Console.WriteLine($"Applying lyrics: {lyricsPath}");

        //     if (!File.Exists(lyricsPath)) {
        //         Console.WriteLine("Lyrics file does not exist.");
        //         return;
        //     }

        //     string[] lyrics = File.ReadAllLines(lyricsPath)
        //                           .SelectMany(line => line.Split(new[] { ' ', '\t', ',', '.', '!', '?' }, StringSplitOptions.RemoveEmptyEntries))
        //                           .ToArray();

        //     if (lyrics.Length == 0) {
        //         Console.WriteLine("No lyrics found in the file.");
        //         return;
        //     }

            
        //     List<UVoicePart> voiceParts = project.parts.OfType<UVoicePart>().ToList();
        //     if (voiceParts.Count == 0) {
        //         Console.WriteLine("No voice parts available in the project.");
        //         return;
        //     }

        //     AssignLyricsToNotes(voiceParts[0], lyrics);


        //     // Add singer to our track
        //     UTrack selectedTrack = project.tracks[0];
        //     Console.WriteLine($"You selected: {selectedTrack.TrackName}");

        //     // List available singers
        //     SingerManager.Inst.SearchAllSingers();
        //     var allSingers = SingerManager.Inst.SingerGroups.SelectMany(g => g.Value).ToList();
        //     if (allSingers.Count == 0) {
        //         Console.WriteLine("No singers available to update the track.");
        //         return;
        //     }

        //     Console.WriteLine("Available singers:");
        //     for (int i = 0; i < allSingers.Count; i++) {
        //         Console.WriteLine($"{i + 1}. {allSingers[i].LocalizedName} ({allSingers[i].SingerType})");
        //     }

        //     USinger selectedSinger = allSingers[0];
        //     Console.WriteLine($"You selected: {selectedSinger.LocalizedName}");

        //     // Update track with new singer
        //     DocManager.Inst.StartUndoGroup();
        //     var singerCommand = new TrackChangeSingerCommand(project, selectedTrack, selectedSinger);
        //     DocManager.Inst.ExecuteCmd(singerCommand);
        //     Console.WriteLine($"Updated singer of track '{selectedTrack.TrackName}' to '{selectedSinger.LocalizedName}'.");

        //     // You can extend this to update phonemizer and renderer here if needed

        //     // Adding Phonemizer
        //     Console.WriteLine("Available phonemizers:");
        //     ListPhonemizers();

        //     string phonemizerName = "OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer";

        //     if (!TryChangePhonemizer(phonemizerName, selectedTrack)) {
        //         Console.WriteLine("Failed to apply phonemizer. Check the name and try again.");
        //     } else {
        //         Console.WriteLine($"Phonemizer {phonemizerName} applied to track {selectedTrack.TrackName}.");
        //     }

        //     DocManager.Inst.EndUndoGroup();
        //     DocManager.Inst.AutoSave();
        //     Console.WriteLine("Track updated and project state saved.");


        //     if (!project.Saved || string.IsNullOrEmpty(project.FilePath)) {
        //         Console.WriteLine("Project is not saved or does not have an existing file path.");


        //         if (string.IsNullOrEmpty(exportPath)) {
        //             Console.WriteLine("No directory path provided. Aborting save operation.");
        //             return;
        //         }

        //         // Combine directory path and project name to form full file path
        //         string fullPath = Path.Combine(exportPath + ".ustx"); // Assuming .ustx as the file extension
        //         project.FilePath = fullPath; // Update the project's file path
        //         SaveProject();
        //     } else {
        //         // Save the project to its existing file path
        //         SaveProject();
        //     }

            

        //     string wavPath = Path.Combine(exportPath + ".wav");
        //     HandleExportWavCommandViaPipeline(wavPath);  // Assuming this method exists for exporting WAV
        //     //try {
        //     //    Console.WriteLine($"Starting WAV export to {wavPath}");
        //     //    if (project.tracks.Count == 0) {
        //     //        Console.WriteLine("No tracks in the project.");
        //     //    }

        //     //    await PlaybackManager.Inst.RenderToFiles(project, wavPath);
        //     //    Console.WriteLine($"Project has been successfully exported to WAV at {wavPath}.");
        //     //} catch (Exception ex) {
        //     //    Console.WriteLine($"An error occurred during the export: {ex.Message}");
        //     //}
        // }



        public static void InitAudio() {
            Log.Information("Initializing audio.");
            if (!OpenUtau.OS.IsWindows() || OpenUtau.Core.Util.Preferences.Default.PreferPortAudio) {
                try {
                    PlaybackManager.Inst.AudioOutput = new OpenUtau.Audio.MiniAudioOutput();
                } catch (Exception e1) {
                    Log.Error(e1, "Failed to init MiniAudio");
                }
            } else {
                try {
                    PlaybackManager.Inst.AudioOutput = new OpenUtau.Audio.NAudioOutput();
                } catch (Exception e2) {
                    Log.Error(e2, "Failed to init NAudio");
                }
            }
            Log.Information("Initialized audio.");
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
            DocManager.Inst.Initialize(); // Ensure DocManager is always initialized before any project loading
            SingerManager.Inst.Initialize();
            InitAudio();

            PromptForProjectLoading();
        }

        static void InitializeCoreComponentsViaPipeline() {
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;
            InitLogging();
            Log.Information($"Data path = {PathManager.Inst.DataPath}");
            Log.Information($"Cache path = {PathManager.Inst.CachePath}");
            Console.WriteLine($"Data path = {PathManager.Inst.DataPath}");
            Console.WriteLine($"Cache path = {PathManager.Inst.CachePath}");
            ToolsManager.Inst.Initialize();
            DocManager.Inst.Initialize(); // Ensure DocManager is always initialized before any project loading
            SingerManager.Inst.Initialize();
            InitAudio();


            /*Starting a new project */
            if (project == null) {
                //DocManager.Inst.Initialize(); // Only initialize if project is not already set
                NewProject();
                //project = DocManager.Inst.Project; // Assign the project instance
            }
        }

        static void PromptForProjectLoading() {
            Console.WriteLine("Do you want to [1] Open an existing project or [2] Start a new project?");
            Console.Write("Select option (1 or 2): ");
            var option = Console.ReadLine();
            switch (option) {
                case "1":
                    HandleOpenProject();
                    break;
                case "2":
                    //if (project == null) {
                    //    DocManager.Inst.Initialize(); // Only initialize if project is not already set
                    //    project = DocManager.Inst.Project; // Assign the project instance
                    //}
                    NewProject();
                    //DocManager.Inst.ExecuteCmd(new LoadProjectNotification(OpenUtau.Core.Format.Ustx.Create()));
                    break;
                default:
                    Console.WriteLine("Invalid option. Starting new project by default.");
                    if (project == null) {
                        DocManager.Inst.Initialize(); // Only initialize if project is not already set
                        project = DocManager.Inst.Project; // Assign the project instance
                    }
                    break;
            }
        }


        //public void InitProject() {
        //    //var args = Environment.GetCommandLineArgs();
        //    //if (args.Length == 2 && File.Exists(args[1])) {
        //        try {
        //            OpenUtau.Core.Format.Formats.LoadProject(new string[] { args[1] });
        //            DocManager.Inst.ExecuteCmd(new VoiceColorRemappingNotification(-1, true));
        //            return;
        //        } catch (Exception e) {
        //            var customEx = new MessageCustomizableException($"Failed to open file {args[1]}", $"<translate:errors.failed.openfile>: {args[1]}", e);
        //            DocManager.Inst.ExecuteCmd(new ErrorMessageNotification(customEx));
        //        }
        //    //}
        //    NewProject();
        //}

        static void NewProject() {
            //var defaultTemplate = Path.Combine(PathManager.Inst.TemplatesPath, "default.ustx");
            //if (File.Exists(defaultTemplate)) {
            //    try {
            //        OpenProject(new[] { defaultTemplate });
            //        DocManager.Inst.Project.Saved = false;
            //        DocManager.Inst.Project.FilePath = string.Empty;
            //        return;
            //    } catch (Exception e) {
            //        var customEx = new MessageCustomizableException("Failed to load default template", "<translate:errors.failed.load>: default template", e);
            //        DocManager.Inst.ExecuteCmd(new ErrorMessageNotification(customEx));
            //    }
            //}
            DocManager.Inst.ExecuteCmd(new LoadProjectNotification(OpenUtau.Core.Format.Ustx.Create()));
            project = DocManager.Inst.Project;
        }

        static void HandleOpenProject() {
            Console.WriteLine("Enter the path to the project file (e.g., project.ustx):");
            string path = Console.ReadLine() ?? string.Empty;
            if (string.IsNullOrEmpty(path)) {
                Console.WriteLine("No path provided.");
                return;
            }
            if (!File.Exists(path)) {
                Console.WriteLine("File does not exist.");
                return;
            }

            path = path.Trim('"').Replace('/', Path.DirectorySeparatorChar);

            Console.WriteLine("Starting to load project...");
            try {
                string[] files = { path };
                DocManager.Inst.ExecuteCmd(new LoadingNotification(typeof(Program), true, "project"));
                OpenUtau.Core.Format.Formats.LoadProject(files);  // This method will handle the actual loading
                project = DocManager.Inst.Project; // Update the global project reference
                DocManager.Inst.ExecuteCmd(new VoiceColorRemappingNotification(-1, true));
                Console.WriteLine("Project opened successfully.");
            } catch (Exception ex) {
                Console.WriteLine($"An error occurred while loading the project: {ex.Message}");
            } finally {
                DocManager.Inst.ExecuteCmd(new LoadingNotification(typeof(Program), false, "project"));
            }
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
                //if (project == null) {
                //    Console.WriteLine("No project is currently loaded.");
                //    return;
                //}
                project = DocManager.Inst.Project;

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


        static void HandleUpdatePhonemizer() {
            project = DocManager.Inst.Project;
            if (project.tracks.Count == 0) {
                Console.WriteLine("No project or tracks loaded. Cannot update a track.");
                return;
            }

            Console.WriteLine("Select a track you want to update phonemizer for :");
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

            Console.WriteLine("Available phonemizers:");
            ListPhonemizers();

            Console.Write("Enter the phonemizer name to apply: ");
            string phonemizerName = Console.ReadLine() ?? "";

            if (!TryChangePhonemizer(phonemizerName, selectedTrack)) {
                Console.WriteLine("Failed to apply phonemizer. Check the name and try again.");
            } else {
                Console.WriteLine($"Phonemizer {phonemizerName} applied to track {selectedTrack.TrackName}.");
            }

        }


        static void HandleUpdateTrack() {
            project = DocManager.Inst.Project;
            if ( project.tracks.Count == 0) {
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

            Console.WriteLine("Available phonemizers:");
            ListPhonemizers();

            Console.Write("Enter the phonemizer name to apply: ");
            string phonemizerName = Console.ReadLine()?? "";

            if (!TryChangePhonemizer(phonemizerName, selectedTrack)) {
                Console.WriteLine("Failed to apply phonemizer. Check the name and try again.");
            } else {
                Console.WriteLine($"Phonemizer {phonemizerName} applied to track {selectedTrack.TrackName}.");
            }

            DocManager.Inst.EndUndoGroup();
            DocManager.Inst.AutoSave();
            Console.WriteLine("Track updated and project state saved.");
        }

        static void ListPhonemizers() {
            var phonemizers = DocManager.Inst.PhonemizerFactories;
            int index = 1;
            foreach (var phonemizer in phonemizers) {
                Console.WriteLine($"{index++}) {phonemizer.type.FullName} - {phonemizer.language}");
            }
        }


        private static bool TryChangePhonemizer(string phonemizerName, UTrack track) {
            try {
                var factory = DocManager.Inst.PhonemizerFactories.FirstOrDefault(factory => factory.type.FullName == phonemizerName);
                var phonemizer = factory?.Create();
                if (phonemizer != null) {
                    DocManager.Inst.ExecuteCmd(new TrackChangePhonemizerCommand(DocManager.Inst.Project, track, phonemizer));
                    return true;
                }
            } catch (Exception e) {
                Log.Error(e, $"Failed to load phonemizer {phonemizerName}");
            }
            return false;
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
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }

            Console.WriteLine($"Adding a new track to the project: {project.name} ({project.FilePath})");

            // List available singers
            SingerManager.Inst.SearchAllSingers();
            var allSingers = SingerManager.Inst.SingerGroups.SelectMany(g => g.Value).ToList();
            if (allSingers.Count == 0) {
                Console.WriteLine("No singers available to add to the track.");
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

            // Create a new track
            var newTrack = new UTrack($"Track {project.tracks.Count + 1}");
            project.tracks.Add(newTrack);
            Console.WriteLine($"New track {newTrack.TrackName} added. Assigning selected singer...");

            DocManager.Inst.StartUndoGroup();
            var singerCommand = new TrackChangeSingerCommand(project, newTrack, selectedSinger);
            DocManager.Inst.ExecuteCmd(singerCommand);
            Console.WriteLine($"Singer {selectedSinger.LocalizedName} added to the new track.");

            // List and select phonemizers
            Console.WriteLine("Available phonemizers:");
            ListPhonemizers();

            Console.Write("Enter the phonemizer name to apply: ");
            string phonemizerName = Console.ReadLine() ?? "";

            if (!TryChangePhonemizer(phonemizerName, newTrack)) {
                Console.WriteLine("Failed to apply phonemizer. Check the name and try again.");
            } else {
                Console.WriteLine($"Phonemizer {phonemizerName} applied to new track.");
            }

            DocManager.Inst.EndUndoGroup();
            DocManager.Inst.AutoSave();
            Console.WriteLine("New track added and project state saved.");
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

        static void ChangeBPM(int num) {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }
            project.tempos[0].bpm = num;
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
            // project.tempos[0].bpm = 94;
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


        static void HandleInstallDependency(string filePath) {
            try {
                if (!File.Exists(filePath)) {
                    Console.WriteLine("Error: Dependency file does not exist.");
                    return;
                }

                Console.WriteLine($"Starting installation of dependency from: {filePath}");

                // Simulate the installation process
                DependencyInstaller.Install(filePath);

                Console.WriteLine("Dependency installed successfully.");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to install dependency: {ex.Message}");
            }
        }

        /*static void HandleOpenProject() {
            *//*if (!DocManager.Inst.ChangesSaved) {
                Console.WriteLine("There are unsaved changes. Save them? (yes/no)");
                if (Console.ReadLine().Trim().ToLower() == "yes") {
                    // Assuming a function that handles saving which you would have implemented.
                    HandleSaveProject();
                }
            }*//*

            Console.WriteLine("Enter the path to the project file (e.g., project.ustx):");
            string path = Console.ReadLine() ?? string.Empty;
            if (string.IsNullOrEmpty(path)) {
                Console.WriteLine("No path provided.");
                return;
            }
            if (!File.Exists(path)) {
                Console.WriteLine("File does not exist.");
                return;
            }

            Console.WriteLine("Starting to load project...");
            try {
                string[] files = { path };
                DocManager.Inst.ExecuteCmd(new LoadingNotification(typeof(Program), true, "project"));
                OpenUtau.Core.Format.Formats.LoadProject(files);  // This method will handle the actual loading
                DocManager.Inst.ExecuteCmd(new VoiceColorRemappingNotification(-1, true)); // Simulate voice color remapping as needed
                Console.WriteLine("Project opened successfully.");
            } catch (Exception ex) {
                Console.WriteLine($"An error occurred while loading the project: {ex.Message}");
            } finally {
                DocManager.Inst.ExecuteCmd(new LoadingNotification(typeof(Program), false, "project"));
            }
        }*/



        static void OpenProject(string[] files) {
            if (files == null || files.Length == 0) {
                Console.WriteLine("No files specified or files array is empty.");
                return;
            }
            try {
                // Mimic loading notification from UI
                Console.WriteLine("Starting to load project...");
                OpenUtau.Core.Format.Formats.LoadProject(files);
                // Mimic remapping notification and other notifications
                Console.WriteLine("Project loaded successfully.");
                // Optionally, update the title or other necessary components
            } catch (Exception ex) {
                Console.WriteLine($"An error occurred while loading the project: {ex.Message}");
            }
        }


        static void HandleSaveCommand() {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }

            if (!project.Saved || string.IsNullOrEmpty(project.FilePath)) {
                Console.WriteLine("Project is not saved or does not have an existing file path.");

                // Get directory path to save the project
                Console.WriteLine("Enter the directory path where you want to save the project:");
                string directoryPath = Console.ReadLine() ?? "";

                if (string.IsNullOrEmpty(directoryPath)) {
                    Console.WriteLine("No directory path provided. Aborting save operation.");
                    return;
                }

                // Get project name from the user
                Console.WriteLine("Enter the name for the project file (without extension):");
                string projectName = Console.ReadLine() ?? "";

                if (string.IsNullOrEmpty(projectName)) {
                    Console.WriteLine("No project name provided. Aborting save operation.");
                    return;
                }

                // Combine directory path and project name to form full file path
                string fullPath = Path.Combine(directoryPath, projectName + ".ustx"); // Assuming .ustx as the file extension
                project.FilePath = fullPath; // Update the project's file path
                SaveProject();
            } else {
                // Save the project to its existing file path
                SaveProject();
            }
        }

        static void RemoveTrack() {
            ListTracks();
            int trackCount = DocManager.Inst.Project.tracks.Count;
            int trackIndex = GetUserInputForTrackRemoval(trackCount);
            var trackToRemove = DocManager.Inst.Project.tracks[trackIndex];

            DocManager.Inst.StartUndoGroup();
            DocManager.Inst.ExecuteCmd(new RemoveTrackCommand(DocManager.Inst.Project, trackToRemove));
            DocManager.Inst.EndUndoGroup();

            Console.WriteLine($"Track '{trackToRemove.TrackName}' has been successfully removed.");
        }

        static int GetUserInputForTrackRemoval(int trackCount) {
            while (true) {
                Console.WriteLine("Enter the number of the track to remove:");
                string input = Console.ReadLine() ?? "";
                if (int.TryParse(input, out int trackNumber) && trackNumber > 0 && trackNumber <= trackCount) {
                    return trackNumber - 1;  // Convert to zero-based index
                }
                Console.WriteLine("Invalid input. Please enter a valid track number.");
            }
        }

        static void ListTracks() {
            var tracks = DocManager.Inst.Project.tracks;
            Console.WriteLine("Available tracks:");
            for (int i = 0; i < tracks.Count; i++) {
                Console.WriteLine($"{i + 1}) {tracks[i].TrackName}");  // Assuming each track has a Name property
            }
        }






        static void SaveProject() {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }
            try {
                project.BeforeSave(); // Assuming the project needs to be preprocessed before saving
                DocManager.Inst.ExecuteCmd(new SaveProjectNotification(project.FilePath)); // Simulate save command
                project.Saved = true; // Mark the project as saved
                Console.WriteLine($"Project saved successfully at {DateTime.Now} to {project.FilePath}");
            } catch (Exception ex) {
                Console.WriteLine($"Failed to save the project: {ex.Message}");
            }
        }


        static async void HandleExportWavCommand() {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }


            if (!project.Saved) {
                Console.WriteLine("The project has unsaved changes. Please save the project before exporting.");
                HandleSaveCommand();
                if (!project.Saved) {
                    Console.WriteLine("Project not saved. Aborting export operation.");
                    return;
                }
            }

            Console.WriteLine("Enter the path where you want to export the WAV file:");
            string exportPath = Console.ReadLine() ?? "";

            if (string.IsNullOrEmpty(exportPath)) {
                Console.WriteLine("No export path provided. Aborting export operation.");
                return;
            }

            try {
                Console.WriteLine($"Starting WAV export to {exportPath}");
                if (project.tracks.Count == 0) {
                    Console.WriteLine("No tracks in the project.");
                }

                await PlaybackManager.Inst.RenderToFiles(project, exportPath);
                Console.WriteLine($"Project has been successfully exported to WAV at {exportPath}.");
            } catch (Exception ex) {
                Console.WriteLine($"An error occurred during the export: {ex.Message}");
            }
        }

        //static async void HandleExportWavCommandViaPipeline(string exportPath) {
        //    if (project == null) {
        //        Console.WriteLine("No project is currently loaded.");
        //        return;
        //    }

        //    //Console.WriteLine($"Starting WAV export to {exportPath}");
        //    //if (project.tracks.Count == 0) {
        //    //    Console.WriteLine("No tracks in the project.");
        //    //}

        //    try {
        //        Console.WriteLine($"Starting WAV export to {exportPath}");
        //        if (project.tracks.Count == 0) {
        //            Console.WriteLine("No tracks in the project.");
        //        }

        //        project = DocManager.Inst.Project;

        //        await PlaybackManager.Inst.RenderToFiles(project, exportPath);
        //        Console.WriteLine($"Project has been successfully exported to WAV at {exportPath}.");
        //    } catch (Exception ex) {
        //        Console.WriteLine($"An error occurred during the export: {ex.Message}");
        //    }

        //    //await PlaybackManager.Inst.RenderToFiles(project, exportPath);
        //    Console.WriteLine($"Project has been successfully exported to WAV at {exportPath}.");
        //}


        //static void SetVoiceColor() {
        //    if (project == null || project.parts.Count == 0) {
        //        Console.WriteLine("No project or parts loaded. Cannot change voice color.");
        //        return;
        //    }

        //    // List parts for user to choose
        //    Console.WriteLine("Select a part to change voice color:");
        //    for (int i = 0; i < project.parts.Count; i++) {
        //        Console.WriteLine($"{i + 1}. {project.parts[i].name} (Track: {project.parts[i].trackNo + 1})");
        //    }

        //    Console.Write("Choose part number: ");
        //    if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
        //        Console.WriteLine("Invalid part number.");
        //        return;
        //    }

        //    UVoicePart selectedPart = project.parts[partIndex - 1] as UVoicePart;
        //    if (selectedPart == null) {
        //        Console.WriteLine("Selected part is not a voice part.");
        //        return;
        //    }

        //    UTrack track = project.tracks[selectedPart.trackNo];

        //    // Fetch all available voice color mappings in the project
        //    var availableColors = project.colorGroups.Select(cg => cg.index).ToList();

        //    if (!availableColors.Any()) {
        //        Console.WriteLine("No available voice color mappings.");
        //        return;
        //    }


        //    // Display voice color options
        //    Console.WriteLine("\nAvailable Voice Color Options:");
        //    foreach (var color in availableColors) {
        //        Console.WriteLine($"  {color}");
        //    }

        //    // Ask user to select a voice color index
        //    Console.Write("\nEnter the voice color index you want to apply (0 to remove voice color): ");
        //    if (!int.TryParse(Console.ReadLine(), out int selectedColorIndex) || (!availableColors.Contains(selectedColorIndex) && selectedColorIndex != 0)) {
        //        Console.WriteLine("Invalid voice color index.");
        //        return;
        //    }

        //    Console.WriteLine($"Applying voice color index {selectedColorIndex} to all phonemes in {selectedPart.name}...");

        //    // Apply the new voice color to all phonemes in the selected part
        //    foreach (UPhoneme phoneme in selectedPart.phonemes) {
        //        var currentExpression = phoneme.GetExpression(DocManager.Inst.Project, track, OpenUtau.Core.Format.Ustx.CLR);
        //        int currentColor = currentExpression.Item1 != null ? (int)currentExpression.Item1 : -1;

        //        // Only update if the color is different from the selected one
        //        if (currentColor != selectedColorIndex) {
        //            DocManager.Inst.ExecuteCmd(new SetPhonemeExpressionCommand(DocManager.Inst.Project, track, selectedPart, phoneme, OpenUtau.Core.Format.Ustx.CLR, selectedColorIndex == 0 ? null : selectedColorIndex));
        //        }
        //    }

        //    Console.WriteLine("Voice color update complete.");
        //}

        //async void ValidateTracksVoiceColor() {
        //    DocManager.Inst.StartUndoGroup();
        //    foreach (var track in DocManager.Inst.Project.tracks) {
        //        if (track.ValidateVoiceColor(out var oldColors, out var newColors)) {
        //            await OpenUtau.App.Views.MainWindow.VoiceColorRemappingAsync(track, oldColors, newColors);
        //        }
        //    }
        //    DocManager.Inst.EndUndoGroup();
        //}


        static void SetVoiceColor() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project or parts loaded. Cannot change voice color.");
                return;
            }

            // List parts for user to choose
            Console.WriteLine("Select a part to change voice color:");
            for (int i = 0; i < project.parts.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.parts[i].name} (Track: {project.parts[i].trackNo + 1})");
            }

            Console.Write("Choose part number: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            UVoicePart selectedPart = project.parts[partIndex - 1] as UVoicePart;
            if (selectedPart == null) {
                Console.WriteLine("Selected part is not a voice part.");
                return;
            }

            UTrack track = project.tracks[selectedPart.trackNo];

            // 🔹 Validate voice color and get old/new color mappings
            if (!track.ValidateVoiceColor(out string[] oldColors, out string[] newColors)) {
                Console.WriteLine("No discrepancies in voice color mappings. No need to update.");
                Console.WriteLine("\nOld Voice Colors:");
                foreach (var color in oldColors) {
                    Console.WriteLine($"  {color}");
                }

                Console.WriteLine("\nNew Suggested Voice Colors:");
                foreach (var color in newColors) {
                    Console.WriteLine($"  {color}");
                }
            }

            //// 🔹 Debug output of old and new voice colors
            //Console.WriteLine("\nOld Voice Colors:");
            //foreach (var color in oldColors) {
            //    Console.WriteLine($"  {color}");
            //}

            //Console.WriteLine("\nNew Suggested Voice Colors:");
            //foreach (var color in newColors) {
            //    Console.WriteLine($"  {color}");
            //}

            if (newColors.Length == 0) {
                Console.WriteLine("No valid new voice color mappings available.");
                return;
            }

            // 🔹 Create mapping view model with validated colors
            VoiceColorMappingViewModel vm = new VoiceColorMappingViewModel(oldColors, newColors, track.TrackName);

            // 🔹 Display available color mappings
            Console.WriteLine("\nAvailable Voice Color Options:");
            for (int i = 0; i < vm.ColorMappings.Count; i++) {
                Console.WriteLine($"  {i}: {vm.ColorMappings[i].OldIndex}");
            }

            // 🔹 Ask user for input
            Console.Write("\nEnter the voice color index you want to apply (0 to remove voice color): ");
            if (!int.TryParse(Console.ReadLine(), out int selectedColorIndex) || selectedColorIndex < 0 || selectedColorIndex >= vm.ColorMappings.Count) {
                Console.WriteLine("Invalid voice color index.");
                return;
            }

            Console.WriteLine($"Applying voice color index {selectedColorIndex} to all phonemes in {selectedPart.name}...");

            // 🔹 Start an undo group for changes
            DocManager.Inst.StartUndoGroup();

            // 🔹 Iterate over phonemes and update voice color using `ValidateVoiceColor()`
            //foreach (UNote note in selectedPart.notes) {
                foreach (UPhoneme phoneme in selectedPart.phonemes) {
                    var tuple = phoneme.GetExpression(project, track, OpenUtau.Core.Format.Ustx.CLR);
                    float? currentColor = tuple.Item1;

                    if (currentColor != selectedColorIndex) {
                        DocManager.Inst.ExecuteCmd(new SetPhonemeExpressionCommand(
                            project,
                            track,
                            selectedPart,
                            phoneme,
                            OpenUtau.Core.Format.Ustx.CLR,
                            selectedColorIndex == 0 ? null : selectedColorIndex
                        ));
                    }
                }
            //}

            // 🔹 End the undo group
            DocManager.Inst.EndUndoGroup();

            Console.WriteLine("Voice color update complete.");
        }






        static void HandlePartInfo() {
            if (project == null || project.parts.Count == 0) {
                Console.WriteLine("No project or parts loaded. Cannot display part info.");
                return;
            }

            // List parts for user to choose
            Console.WriteLine("Select a part to view info:");
            for (int i = 0; i < project.parts.Count; i++) {
                Console.WriteLine($"{i + 1}. {project.parts[i].name} (Track: {project.parts[i].trackNo + 1})");
            }

            Console.Write("Choose part number: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > project.parts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            UVoicePart selectedPart = project.parts[partIndex - 1] as UVoicePart;
            UTrack selectedTrack = project.tracks[selectedPart.trackNo - 1];
            if (selectedPart == null) {
                Console.WriteLine("Selected part is not a voice part.");
                return;
            }

            Console.WriteLine($"\nDetails for part: {selectedPart.name}");
            Console.WriteLine($"Track: {selectedPart.trackNo + 1}, Position: {selectedPart.position}, Duration: {selectedPart.Duration}");
            Console.WriteLine($"Number of Notes: {selectedPart.notes.Count}\n");

            foreach (UNote note in selectedPart.notes) {
                Console.WriteLine($"Note - Position: {note.position}, Duration: {note.duration}, Tone: {note.tone}, Lyric: \"{note.lyric}\"");

                // Display Phoneme Expressions
                if (note.phonemeExpressions.Count > 0) {
                    Console.WriteLine($"  Phoneme Expressions: {string.Join(", ", note.phonemeExpressions.Select(e => $"{e.abbr}:{e.value}"))}");
                } else {
                    Console.WriteLine("  Phoneme Expressions: None");
                }

                // Display Phoneme Overrides
                if (note.phonemeOverrides.Count > 0) {
                    Console.WriteLine($"  Phoneme Overrides: {string.Join(", ", note.phonemeOverrides.Select(o => $"Index: {o.index}, Phoneme: {o.phoneme}"))}");
                } else {
                    Console.WriteLine("  Phoneme Overrides: None");
                }

                Console.WriteLine();
            }

            foreach (UPhoneme phoneme in selectedPart.phonemes) {
                var tuple = phoneme.GetExpression(DocManager.Inst.Project, selectedTrack, OpenUtau.Core.Format.Ustx.CLR);
                if (tuple.Item1 != null) {
                    Console.WriteLine($"  Phoneme: \"{phoneme.phoneme}\" -> Voice Color Index: {tuple.Item1}");
                } else {
                    Console.WriteLine($"  Phoneme: \"{phoneme.phoneme}\" -> No Voice Color Mapping");
                }
            }


        }



        static void HandleLyricsCommand(string filePath) {
            if (project == null) {
                Console.WriteLine("No project is currently loaded.");
                return;
            }

            if (!File.Exists(filePath)) {
                Console.WriteLine("Lyrics file does not exist.");
                return;
            }

            string[] lyrics = File.ReadAllLines(filePath)
                                  .SelectMany(line => line.Split(new[] { ' ', '\t', ',', '.', '!', '?' }, StringSplitOptions.RemoveEmptyEntries))
                                  .ToArray();

            if (lyrics.Length == 0) {
                Console.WriteLine("No lyrics found in the file.");
                return;
            }

            List<UVoicePart> voiceParts = project.parts.OfType<UVoicePart>().ToList();
            if (voiceParts.Count == 0) {
                Console.WriteLine("No voice parts available in the project.");
                return;
            }

            for (int i = 0; i < voiceParts.Count; i++) {
                Console.WriteLine($"{i + 1}: {voiceParts[i].name} (Start: {voiceParts[i].position}, Duration: {voiceParts[i].Duration})");
            }

            Console.Write("Select a part number to add lyrics: ");
            if (!int.TryParse(Console.ReadLine(), out int partIndex) || partIndex < 1 || partIndex > voiceParts.Count) {
                Console.WriteLine("Invalid part number.");
                return;
            }

            AssignLyricsToNotes(voiceParts[partIndex - 1], lyrics);
        }

        static void AssignLyricsToNotes(UVoicePart voicePart, string[] lyrics) {
            int noteCount = voicePart.notes.Count;
            int lyricsIndex = 0;

            foreach (UNote note in voicePart.notes) {
                note.lyric = lyricsIndex < lyrics.Length ? lyrics[lyricsIndex++] : "a";
            }

            Console.WriteLine($"Lyrics assigned to {voicePart.name}. Excess lyrics: {Math.Max(0, lyrics.Length - noteCount)}");
        }







        static void HandleLoadRenderedPitch() {
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
            var selectedPart = project.parts.FirstOrDefault(p => p is UVoicePart) as UVoicePart;
            if (!(selectedPart is UVoicePart voicePart)) {
                Console.WriteLine("Selected part is not a voice part.");
                return;
            }
            List<UNote> notesList = new List<UNote>(voicePart.notes);
            // var batchEdit = new Transpose(2, "Transpose Octave Up");
            // batchEdit.Run(project, selectedPart, selectedPart.notes.ToList(), DocManager.Inst);
            LoadRenderedPitch pitchLoader = new LoadRenderedPitch();
            pitchLoader.Run(project, selectedPart, selectedPart.notes.ToList(), DocManager.Inst); 
            Console.WriteLine("Batch edit completed.");
            // Assuming LoadRenderedPitch is a method that needs to be implemented or a class that needs to be instantiated and run
            Console.WriteLine("Rendered pitch loading completed for selected part.");
        }

        static void HandleTranspose(int num) {
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
            var selectedPart = project.parts.FirstOrDefault(p => p is UVoicePart) as UVoicePart;
            if (!(selectedPart is UVoicePart voicePart)) {
                Console.WriteLine("Selected part is not a voice part.");
                return;
            }
            List<UNote> notesList = new List<UNote>(voicePart.notes);
            var batchEdit = new Transpose(num, "Transpose Octave Up");
            batchEdit.Run(project, selectedPart, selectedPart.notes.ToList(), DocManager.Inst);
        }





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

        /*static void ShowHelp() {
            Console.WriteLine("OpenUtau Command Line Interface (CLI) Usage:");
            Console.WriteLine("  --init          Initializes and sets up the OpenUtau CLI environment.");
            Console.WriteLine("  --install       Installs singers or dependencies:");
            Console.WriteLine("       --singer [format] [path]     Installs a singer from the specified path with the given format.");
            Console.WriteLine("       --dependency [path]          Installs a dependency from the specified path.");
            Console.WriteLine("  --singer        Lists all available singers.");
            Console.WriteLine("  --track         Manages tracks within the project:");
            Console.WriteLine("       --add          Adds a new track.");
            Console.WriteLine("       --list         Lists all tracks in the current project.");
            Console.WriteLine("       --update       Updates an existing track.");
            Console.WriteLine("       --remove       Removes an existing track.");
            Console.WriteLine("  --part          Manages parts within the project:");
            Console.WriteLine("       --add          Adds a new part to a track.");
            Console.WriteLine("       --delete       Deletes an existing part from a track.");
            Console.WriteLine("       --rename       Renames an existing part.");
            Console.WriteLine("       --list         Lists all parts in the current project.");
            Console.WriteLine("  --import        Imports data into the project:");
            Console.WriteLine("       --midi [path]  Imports MIDI data from the specified path.");
            Console.WriteLine("  --phonemizers   Lists all available phonemizers.");
            Console.WriteLine("  --export        Exports the current project:");
            Console.WriteLine("       --wav          Exports the project to a WAV file at the specified path.");
            Console.WriteLine("  --save          Saves the current project.");
            Console.WriteLine("  --lyrics [path] Applies lyrics from a specified file to a part in the project.");
            Console.WriteLine("  --exit          Exits the OpenUtau CLI.");
            Console.WriteLine("For more details on each command, type the command followed by '--help'.");
        }*/


        static void ShowHelp(string? command = null) {
            if (string.IsNullOrEmpty(command)) {
                // General help overview
                Console.WriteLine("OpenUtau Command Line Interface (CLI) Usage:");
                Console.WriteLine("  --init          Initializes the CLI environment.");
                Console.WriteLine("  --install       Install components like singers or dependencies.");
                Console.WriteLine("  --singer        Manage and list singers.");
                Console.WriteLine("  --track         Operations for managing tracks.");
                Console.WriteLine("  --part          Operations for managing parts within tracks.");
                Console.WriteLine("  --import        Import external data into the project.");
                Console.WriteLine("  --export        Export project to different formats.");
                Console.WriteLine("  --save          Save the current project.");
                Console.WriteLine("  --lyrics        Apply lyrics to parts.");
                Console.WriteLine("  --exit          Exit the CLI.");
                Console.WriteLine("Use '--help [command]' for more details on a specific command, e.g., '--help --track'");
            } else {
                // Detailed help for a specific command
                switch (command.ToLower()) {
                    case "--init":
                        Console.WriteLine("  --init: Initializes and sets up the OpenUtau CLI environment. Must be run first.");
                        break;
                    case "--install":
                        Console.WriteLine("  --install: Installs components necessary for the project.");
                        Console.WriteLine("    --singer [format] [path]: Installs a singer from a specified path.");
                        Console.WriteLine("    --dependency [path]: Installs a dependency from a specified path.");
                        break;
                    case "--singer":
                        Console.WriteLine("  --singer: Lists all installed singers and manages singer settings.");
                        break;
                    case "--track":
                        Console.WriteLine("  --track: Manages tracks within the project.");
                        Console.WriteLine("    --add: Adds a new track.");
                        Console.WriteLine("    --list: Lists all tracks.");
                        Console.WriteLine("    --update: Updates settings for a selected track.");
                        Console.WriteLine("    --remove: Removes a specified track.");
                        break;
                    case "--part":
                        Console.WriteLine("  --part: Manages parts within tracks.");
                        Console.WriteLine("    --add: Adds a new part to a track.");
                        Console.WriteLine("    --delete: Deletes a part from a track.");
                        Console.WriteLine("    --rename: Renames a part.");
                        Console.WriteLine("    --list: Lists all parts.");
                        break;
                    case "--import":
                        Console.WriteLine("  --import: Imports data into the project.");
                        Console.WriteLine("    --midi [path]: Imports MIDI data from a path.");
                        break;
                    case "--export":
                        Console.WriteLine("  --export: Exports the project in different formats.");
                        Console.WriteLine("    --wav [path]: Exports the project as a WAV file to a specified path.");
                        break;
                    case "--save":
                        Console.WriteLine("  --save: Saves the current state of the project to disk.");
                        break;
                    case "--lyrics":
                        Console.WriteLine("  --lyrics [path]: Applies lyrics from a specified file to a part in the project.");
                        break;
                    case "--exit":
                        Console.WriteLine("  --exit: Exits the CLI and ensures all changes are saved or prompts if unsaved.");
                        break;
                    default:
                        Console.WriteLine($"No detailed help available for '{command}'.");
                        break;
                }
            }
        }


    }
}
