
from manim import *

class SlideScene_3(Scene):
    def construct(self):
        config.background_color = BLACK  # will be swapped below if theme is dark
        title = Text("Third Law: Action & Reaction", font_size=48)
        title.to_edge(UP)
        self.play(Write(title), run_time=1)

        bullets = VGroup()
        b0 = Text("For every action...", font_size=36)
        b0.next_to(title, DOWN, buff=1.0)
        bullets.add(b0)
        b1 = Text("...there is an equal and opposite reaction", font_size=36)
        b1.next_to(title, DOWN, buff=1.6)
        bullets.add(b1)
        b2 = Text("Think of a rocket launch!", font_size=36)
        b2.next_to(title, DOWN, buff=2.2)
        bullets.add(b2)

        self.wait(0.2)
        self.play(FadeIn(b0), run_time=4.0594)
        self.wait(0.2)
        self.play(FadeIn(b1), run_time=4.0594)
        self.wait(0.2)
        self.play(FadeIn(b2), run_time=4.0594)
        self.wait(0.5)

        for mob in self.mobjects:
            if isinstance(mob, Text):
                mob.set_color(WHITE)
