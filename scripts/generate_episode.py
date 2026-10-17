#!/usr/bin/env python3
"""Rotate through original child-safe safari story blueprints without paid APIs."""
import json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "episode.json"
HISTORY = ROOT / "data/episode_history.json"

STORIES = [
 ("sharing_mangoes", "Leo Learns to Share", "sharing and kindness",
  "Leo finds three mangoes, but his friends arrive hungry too.",
  [
   ("On a bright safari morning, Leo the little lion discovers three ripe mangoes beneath the acacia tree.", "Leo finds a tasty surprise!"),
   ("Ellie the elephant and Gigi the giraffe arrive. They are hungry, and Leo has a difficult choice to make.", "His friends are hungry too."),
   ("Leo hugs the mangoes close, then notices his friends waiting kindly and thinks about friendship.", "What would a good friend do?"),
   ("Leo invites Ellie and Gigi to share. They take turns and discover that a shared treat feels even sweeter.", "Sharing makes the moment sweeter!"),
   ("The friends enjoy their snack together. Leo learns that kindness can turn a small treat into a wonderful memory.", "Kindness makes friendship grow!")
  ]),
 ("teamwork_mango", "The Safari Friends Work Together", "teamwork and problem-solving",
  "A mango rolls away before snack time. Can the friends solve the problem together?",
  [
   ("Leo spots three golden mangoes near the acacia tree and calls his friends over for a safari snack.", "Snack time on the savanna!"),
   ("One mango rolls down a little hill and stops beside tall grass. The friends look at one another.", "Oh no, the mango rolled away!"),
   ("Leo tries to reach it, but it is too far. Ellie has an idea, and Gigi looks for a safe path.", "Everyone has an idea."),
   ("Gigi points out the path, Ellie gently nudges the mango, and Leo catches it safely.", "Teamwork solves the problem!"),
   ("The friends celebrate and share their snack. They learn that listening to one another makes hard jobs easier.", "Together, we can do more!")
  ]),
 ("patient_turns", "Leo Learns to Take Turns", "patience and fairness",
  "Leo wants the first mango right away, but his friends suggest a fair way to take turns.",
  [
   ("Leo finds three delicious mangoes and feels excited to taste the sweetest one first.", "Leo can hardly wait!"),
   ("Ellie and Gigi arrive, and both friends would like a turn choosing a mango too.", "Everyone wants a turn."),
   ("Leo starts to rush, then pauses when Ellie suggests they take turns fairly.", "A little patience helps."),
   ("The friends choose one at a time and make sure everybody gets a fair share.", "Taking turns is fair!"),
   ("Their snack becomes a happy moment for all three friends. Leo discovers that waiting can be worth it.", "Good things come to patient friends!")
  ]),
 ("gigi_honesty", "Gigi Tells the Truth", "honesty and responsibility",
  "When a mango rolls away, Gigi chooses to tell her friends what happened.",
  [
   ("Leo arranges three ripe mangoes for a snack while Ellie and Gigi settle under the acacia tree.", "A safari snack is ready!"),
   ("Gigi accidentally bumps one mango, and it rolls into the grass. She feels worried.", "Oops! A mango rolled away."),
   ("Gigi takes a breath and tells Leo honestly what happened, even though she feels nervous.", "Telling the truth takes courage."),
   ("Leo thanks Gigi for being honest. Together, they find the mango and check that it is clean and safe.", "Honesty helps friends trust."),
   ("The friends continue their day with smiles. Gigi learns that telling the truth helps solve problems.", "Honesty builds trust!")
  ]),
 ("ellie_kindness", "Ellie's Little Act of Kindness", "empathy and helping others",
  "Ellie notices Gigi is being left out and helps the friends welcome everyone.",
  [
   ("Leo discovers three mangoes beneath the tree and invites Ellie to join him for a snack.", "A little surprise for friends!"),
   ("Gigi arrives later and stands quietly nearby, unsure whether there is room for her.", "Gigi feels left out."),
   ("Ellie notices Gigi's expression and reminds Leo that a good friend makes everyone welcome.", "Notice how your friends feel."),
   ("Leo welcomes Gigi, and the three friends arrange the mangoes so everyone can join in.", "Make room for everyone."),
   ("Gigi smiles and joins the conversation. Ellie shows that one small kind action can change someone's day.", "A little kindness means a lot!")
  ]),
 ("curious_safari", "Leo's Curious Safari Question", "curiosity and early learning",
  "Leo wonders why mangoes grow on trees, turning snack time into a learning adventure.",
  [
   ("Leo finds three mangoes and wonders how such sweet fruit grows on a tree in the sunny savanna.", "Leo has a big question!"),
   ("Ellie and Gigi join him, and each friend shares an idea about where fruit comes from.", "Let's think and learn together."),
   ("They look at the branches and notice leaves and the places where fruit can grow.", "Trees help fruit grow."),
   ("The friends talk about sunlight, water, and time, learning that plants need care to grow.", "Sunlight and water help plants."),
   ("Leo is proud of his question. The friends learn that curiosity helps us discover the world.", "Keep asking curious questions!")
  ])
]

def main():
    try:
        history = json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        history = []
    choices = [s for s in STORIES if s[0] not in history[-3:]] or STORIES
    story = random.choice(choices)
    slug, title, theme, hook, lines = story
    starts, ends = [0, 8, 16, 24, 32], [8, 16, 24, 32, 40]
    episode = {
      "episode_id": re.sub(r"[^a-z0-9]+", "_", slug.lower()).strip("_"),
      "title": f"{title} | Little Safari Friends",
      "description": f"{hook}\n\nAn original Little Safari Friends story about {theme}, featuring Leo the little lion, Ellie the elephant and Gigi the giraffe. Made for young children and families.\n\nSubscribe for more gentle animal adventures, friendship stories and positive lessons.\n\n#LittleSafariFriends #KidsStories #AnimalStories #PreschoolStories",
      "theme": theme, "voice": "en-US-AnaNeural", "width": 1280, "height": 720,
      "resolution_percentage": 100, "render_samples": 16, "fps": 24,
      "duration_seconds": 40,
      "scenes": [{"start": starts[i], "end": ends[i], "narration": n, "caption": c}
                 for i, (n, c) in enumerate(lines)]
    }
    EPISODE.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps((history + [slug])[-20:], indent=2) + "\n", encoding="utf-8")
    print(f"Generated: {episode['title']} | theme: {theme} | 5 scenes")

if __name__ == "__main__":
    main()
