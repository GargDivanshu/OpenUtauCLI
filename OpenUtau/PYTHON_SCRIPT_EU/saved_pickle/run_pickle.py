
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from isobar import *
from helpers import load_markov_model

note_markov = load_markov_model("note_markov.pkl")
dur_markov = load_markov_model("dur_markov.pkl")
amp_markov = load_markov_model("amp_markov.pkl")

timeline = Timeline(120)
timeline.stop_when_done = True
timeline.schedule({
    "note": note_markov,
    "duration": dur_markov,
    "amplitude": amp_markov
})

timeline.run()
