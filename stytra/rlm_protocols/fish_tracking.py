from stytra import Stytra
from stytra.stimulation.stimuli import (
    FishTrackingStimulus,
    HalfFieldStimulus,
    RadialSineStimulus,
    FullFieldVisualStimulus,
    FishOverlayStimulus,
    FishOverlayStimulus3,
)
from stytra.stimulation.stimuli.conditional import CenteringWrapper, SingleConditionalWrapper, PauseOutsideStimulus

from stytra.stimulation import Protocol
from lightparam import Param
from pathlib import Path


class FollowProtocol(Protocol):
    name = "follow"
    stytra_config = dict(
        display=dict(min_framerate=50),
        tracking=dict(method="fish", embedded=False, estimator="position"),
        #camera=dict(video_file=str(Path(__file__).parent / "assets" / "fish_free_compressed.h5"),min_framerate=100),
        #camera=dict(video_file=str("/Users/mlb/Desktop/shoals_DT_mix_12 ind.avi"),min_framerate=50,),
        camera=dict(video_file=str("/Users/Ray/Downloads/Double_fish.mp4"),
        min_framerate=50,),
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
        self.n_fish_display = Param(4, (1, 12))
        

    def get_stim_sequence(self):
        stimuli = []
        # The phototaxis stimulus for zebrafish is bright on one side of the
        # fish and dark on the other. The type function combines two classes:
        stim = type("follow", (FishTrackingStimulus, FishOverlayStimulus3), {})

        # The stimuli are a sequence of a phototactic stimulus and full-field
        # illumination

        offset_xlist = [50, 0, 50, -50, 20, -50, 0, 50, 0, 75, -75, 75, -75, 100]
        offset_ylist = [0, 50, 50, -50, 0, 50, -20, 20, -50, 75, -75, 25, 50, 0]

        x_offset = []
        x_offset.extend(offset_xlist[0:self.n_fish_display])
        y_offset = []
        y_offset.extend(offset_ylist[0:self.n_fish_display])


        for i in range(self.n_trials):

            # The stimulus of interest is wrapped in a CenteringStimulus,
            # so if the fish moves out of the field of view, a stimulus is
            # displayed which brings it back
            stimuli.append(
                PauseOutsideStimulus(
                stim=stim(duration=self.stim_on_duration,color=(self.brightness,) * 3, x_offset = x_offset, y_offset = y_offset, n_fish_display=self.n_fish_display
                    ), reset_phase=0,
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
