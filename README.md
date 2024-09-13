
# OpenUtauCLI

This project is a modification of OpenUtau, where it allows the user to use OpenUtau via CLI commands

The objective of this project is to automate the task of inferencing. 

This project is built on top of OpenUtau by stakira
- [OpenUtau](https://github.com/stakira/OpenUtau)

- Though this documentation is made keeping in mind the fact, no new joinee should face any issue, but if the problem comes up do lemme know


## Downloading the VoiceBanks

### Download the zip files and just directly use the zip file to install a singer in OpenUtau ( remember there is no need to unzip it )

- https://drive.google.com/file/d/1N9B40P4ifokBn7sEu5WSzzraKfaJGuDK/view?usp=drive_link
- https://drive.google.com/file/d/1ZzCwlD9aaKfbcfHGh0f1DWkkHpwOw3pl/view?usp=drive_link
- https://drive.google.com/file/d/17pwVIivDHZnn3bancbCz7qNptL-wxZCo/view?usp=drive_link
- https://drive.google.com/file/d/1erqO1PdjJatAWqgBvfZ8VvvUGeu0rBHp/view?usp=drive_link

## Running the project

## In Dev Mode: 

- move to `OpenUtau/bin/Debug/net6.0-windows`
- Build the `OpenUtua/Program.cs`
- `.\OpenUtau.exe --init`


## using Docker

#### Don't forget to start Docker Desktop before running docker cmds

### Building the Docker Image

```bash
docker build -t openutau .
```

### Running the Docker Container


```bash
docker run -it openutau
```

## High level Code Flow & Potential issues


- we take up reference song details like midi, now the song has lot of elements like vocal, bass, upbeat, rhythmic tracks, we are not getting proper midi for vocal to work with, this cleanup is one roadblock. It is doable, but needs to be very correct in our workflow.
- upon getting midi, the lyrics we are generating with LLM, in a way by paraphrasing the lyrics of original song and feeding original melody info like velocity, stress,
  note duration etc, the lyrics are still not fitting up properly to the system. by this i mean, the words may not be clear at all, like what is being sung, or the “feel”
  is off, which could be due to mismatch of our syllable and phonetic mismatch.

  The core issue is that, even after feeding a lot of reference of original song, like velocity, note duration, timing, chord at which it is played, if the generated lyric is “Jingle, Jingle, It is Christmas eve” , then from singing pov “It is” is not helping us in any way, we need some mechanism to either tweak midi to fit it, or maybe some mech to tweak the lyric to remove “it is” and make the decision of “Jingle, Jingle, Christmas Eve” 
- We till now have no mechanism or algorithm to tweak the midi notes, pitch, or other (which we are not aware of) relevant parameters to fit the lyrics. Right now, our approach is tweaking with the lyrics and not the midi on which we are adding our lyrics.
- So, OpenUtau takes up midi and lyrics and though we can feed the lyrics at one go, and have generated automated results previously as well, one thing to note in our software is that it has its own syntax to : 

a) extend a word to multiple succeeding notes, it uses → + 

b) club many words together in one midi note, it uses → "word1 word2" 

c) simply add different words in succeeding midi notes → just add word1 to note1 , word2 to note2, word3 to note3, and so on. 


We need a way for : 

a) either LLM to understand the midi, and determine where these lyric adjustments are required and hence give us lyrics with proper formatted lyric in our way. 

b) or to it just simply give us lyric, we add it to midi, and then use some midi manipulation algorithm (maybe, like Q Audio DSP Library) which can process this generated song. 


In this meeting, we are going to discuss a few repos which we found and others which you might want to refer us. 

## Using the Application (Step wise manner)

- Run the project either in Docker run cmd or the dev mode
- Add the select by using `--install --singer [format] [path]`, in which format includes either of ["Diffsinger", "Vogeon"] etc type of Singers and `[path]` being the path of singer file. (one time process, doesn't need to be executed again and again)
- NOTE: We were using DiffSinger models for this project, so always select the Diffsinger cause we were using DiffSinger models.
- Also install the dependency using `--install --dependency [path]` where `[path]` is the local path of the dependency in your system. The dependencies are going to be oudep files which help in the overall functioning of the application.
- use `--track --list` to list the current default empty track which appears at the beginning of the project.
- use `--track --add` to add a new track, then update the track using `--track --update`.
- To update select the singer you want to use, then add the name of the phonemizer you want (for English select the `OpenUtau.Core.DiffSinger.DiffSingerEnglishPhonemizer`), Diffsinger gets selected automatically as the renderer. 
- Import Midi file, containing the melody of the song using `--import --midi [path]`, where `[path]` being the path od midi file. Make sure the midi file consists of only the vocal parts of the song and is isolated from the background music and other rhythmic, instrumental tracks.
- then add lyrics to the midi by `--lyrics [path]`, where `[path]` being the `.txt` file containing the lyrics.
- before saving the project ensure that there are no empty tracks present in the project, by listing `--track --list` and checking for now many tracks are there and also by `--part --list` to check what parts are present and in what track. If any track appears to be containing no part, then remove it by `--track --remove`.
- save the project using `--save`
- Export the wav file of the generated song using `--export --wav [path]` where `[path]` being the dir where you want to save the project

## Outputs 


### Below these were made manually with a GUI to get an understanding of OpenUtau and to see how good these available VoiceBanks are

https://github.com/user-attachments/assets/9b0f1c5c-7974-4d46-9f1e-ff38a42d7e87



https://github.com/user-attachments/assets/c568cd57-2d1c-463f-b66a-7429fb208c88



https://github.com/user-attachments/assets/4300f009-2a5c-4c8d-8129-916216e8f378


### Below outputs were generated via CLI app and then improved upon later on manually to propery fit in the lyrics to respective midi notes



https://github.com/user-attachments/assets/f75ff56b-96f6-434b-9784-c756c58b871a



https://github.com/user-attachments/assets/5e015d9f-7cf9-494e-9c91-eedcb223f1d6





## CLI Commands

### Commands Overview

1) `.\OpenUtau.exe --init`
Initializes the CLI environment. This command must be run first before any other operations.

2) `--install`
Installs necessary components for the project.

  #### Subcommands:
  - `--singer [format] [path]` : Installs a singer from the specified path.

  - `--dependency [path]` : Installs a dependency from the specified path.

  - `--singer` : Lists all installed singers and manages singer settings.

4) `--track`
Manages tracks within the project.

  #### Subcommands:
  - `--add` : Adds a new track to the project.

  - `--list` : Lists all tracks in the current project.

  - `--update` : Updates settings for a selected track.

  - `--remove` : Removes a specified track from the project.

5) `--part`
Manages parts within tracks.

  #### Subcommands:
  - `--add` : Adds a new part to a selected track.

  - `--delete` : Deletes a part from a selected track.

  - `--rename` : Renames a part in the selected track.

  - `--list` : Lists all parts within the project.

6) `--import`
Imports external data into the project.

  #### Subcommands:
  - `--midi [path]` : Imports MIDI data from the specified path.

7) `--export`
Exports the project to different formats.

  #### Subcommands:

  - `--wav [path]` : Exports the project as a WAV file to the specified path.

8) `--save`
Saves the current state of the project to disk.

9) `--lyrics`
Applies lyrics to parts within the project.

  #### Subcommands:

  - `--lyrics [path]` : Applies lyrics from the specified file to a part in the project.  

10) `--exit`
Exits the CLI. It ensures all changes are saved, or it will prompt if there are unsaved changes.
