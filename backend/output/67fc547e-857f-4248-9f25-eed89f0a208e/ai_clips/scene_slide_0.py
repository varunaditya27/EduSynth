
from manim import *

class SlideScene_0(Scene):
    def construct(self):
        config.background_color = BLACK  # will be swapped below if theme is dark
        title = Text("What is a Motherboard?", font_size=48)
        title.to_edge(UP)
        self.play(Write(title), run_time=1)

        bullets = VGroup()
        b0 = Text("The main circuit board", font_size=36)
        b0.next_to(title, DOWN, buff=1.0)
        bullets.add(b0)
        b1 = Text("Connects all computer parts", font_size=36)
        b1.next_to(title, DOWN, buff=1.6)
        bullets.add(b1)
        b2 = Text("The computer's 'backbone'", font_size=36)
        b2.next_to(title, DOWN, buff=2.2)
        bullets.add(b2)

        self.wait(0.2)
        self.play(FadeIn(b0), run_time=2.21)
        self.wait(0.2)
        self.play(FadeIn(b1), run_time=2.21)
        self.wait(0.2)
        self.play(FadeIn(b2), run_time=2.21)
        self.wait(0.5)

        for mob in self.mobjects:
            if isinstance(mob, Text):
                mob.set_color(WHITE)
