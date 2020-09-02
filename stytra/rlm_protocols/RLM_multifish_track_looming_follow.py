import numpy as np
import pandas as pd

from stytra import Stytra
from stytra.stimulation.stimuli import (
    FishTrackingStimulus,
    DoubleFishTrackingStimulus,
    FullFieldVisualStimulus,
    DoubleFishOverlayStimulus,
    CombinerStimulus,
    InterpolatedStimulus, 
    DoubleFishOverlayStimulus,
)
from stytra.stimulation.stimuli.visual import MultiTrackingCircleStimulus
from stytra.stimulation.stimuli.conditional import PauseOutsideStimulus, DoublePauseOutsideStimulus

from stytra.stimulation import Protocol
from lightparam import Param
from pathlib import Path

class LoomingFollowStimulus(InterpolatedStimulus, MultiTrackingCircleStimulus):
    name = "looming_follow_stimulus"


class FollowProtocol(Protocol):
    name = "follow"
    stytra_config = dict(
        display=dict(min_framerate=50),
        tracking=dict(method="fish", embedded=False, estimator="doubleposition"),
        #camera=dict(video_file=str(Path(__file__).parent / "assets" / "fish_free_compressed.h5"),min_framerate=100),
        #camera=dict(video_file=str("/Users/mlb/Desktop/shoals_DT_mix_12 ind.avi"),min_framerate=50,),
        #camera=dict(video_file=str("/Users/mlb/Desktop/Free_swim_fish_ex.mp4"),min_framerate=50,),
        camera=dict(video_file=str("/Users/Ray/Downloads/Double_fish.mp4"),min_framerate=50,),
    )

    def __init__(self):
        super().__init__()
        self.n_trials = Param(20, (0, 2400))
        self.stim_on_duration = Param(10, (0, 30))
        self.stim_off_duration = Param(10, (0, 30))
        self.center_offset = Param(0, (-100, 100))
        self.brightness = Param(255, (0, 255))
        self.stim_on = Param(4, (0, 30))
        self.stim_off = Param(4, (0, 30))
        self.n_looms = Param(10, limits=(0, 1000))
        self.max_loom_size = Param(30, limits=(0, 100))
        self.max_loom_duration = Param(50, limits=(0, 100))
        self.x_pos_pix = Param(10, limits=(0, 2000))
        self.y_pos_pix = Param(10, limits=(0, 2000))

    def get_stim_sequence(self):
        stimuli = []
        # The phototaxis stimulus for zebrafish is bright on one side of the
        # fish and dark on the other. The type function combines two classes:
        stim = type("follow", (DoubleFishTrackingStimulus, DoubleFishOverlayStimulus), {})
        stimloom = type("follow", (DoubleFishTrackingStimulus, LoomingFollowStimulus), {})
        #stim_list = stim, LoomingStimulus
                    
               
        # The stimuli are a sequence of a phototactic stimulus and full-field
        # illumination
        for i in range(self.n_trials):

            # The stimulus of interest is wrapped in a CenteringStimulus,
            # so if the fish moves out of the field of view, a stimulus is
            # displayed which brings it back

            radius_df = pd.DataFrame(
                dict(
                    t=[0, np.random.rand() * self.max_loom_duration],
                    radius=[0, np.random.rand() * self.max_loom_size],
                )
            )

            stim1 = stim(duration=self.stim_on_duration,color=(0, 0, 0))
            stim2 = stimloom(
                    background_color=(0, 0, 0),
                    circle_color=(255, 255, 255),
                    df_param=radius_df,
                    origin=(10,10))
            
            stimuli.append(
                DoublePauseOutsideStimulus(
                stim=CombinerStimulus([stim1, stim2]), reset_phase=0,
                )
            )

            stimuli.append(
                FullFieldVisualStimulus(
                    color=(self.brightness,) * 3, duration=self.stim_off_duration
                )
            )

        return stimuli


if __name__ == "__main__":
    s = Stytra(protocol=FollowProtocol())
