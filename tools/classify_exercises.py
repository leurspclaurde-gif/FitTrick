"""Build exercise_meta.csv from exercises_from_history.csv.

Every exercise (history + added) has an explicit, hand-written spec line below,
so no row relies on a keyword fallback. Numeric defaults come from a profile code.

Spec line: Name | Primary | Secondary | Equipment | Load | Implements | Type | Mechanics | Profile | Instruction
  - muscles / equipment use the abbreviations in M and E; lists are comma separated
  - Type: W=Weighted B=Bodyweight T=Timed C=Cardio ; Mechanics: C=Compound I=Isolation
  - Profile: key of PROFILES, or explicit "RepMin,RepMax,Sets,RestSec,SecPerRep" in brackets

Run:  python -I classify_exercises.py
"""
import csv
import os
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "exercises_from_history.csv")
DST = os.path.join(HERE, "exercise_meta.csv")

M = {
    "CH": "Chest", "FD": "Front Delts", "SD": "Side Delts", "RD": "Rear Delts", "TRI": "Triceps",
    "BI": "Biceps", "FA": "Forearms", "LAT": "Lats", "UB": "Upper Back", "TRP": "Traps",
    "LB": "Lower Back", "ABS": "Abs", "OBL": "Obliques", "Q": "Quads", "HM": "Hamstrings",
    "GL": "Glutes", "ADD": "Adductors", "ABD": "Abductors", "CAL": "Calves", "CAR": "Cardio",
    "MOB": "Mobility",
}
E = {
    "BW": "Bodyweight", "MAT": "Mat", "DB": "Dumbbell", "BB": "Barbell", "EZ": "EZ-Bar",
    "TB": "Trap Bar", "KB": "Kettlebell", "CA": "Cable", "MA": "Machine", "SM": "Smith Machine",
    "LP": "Leg Press", "HSQ": "Hack Squat", "HST": "Hammer Strength", "BN": "Bench",
    "IBN": "Incline Bench", "DBN": "Decline Bench", "PBN": "Preacher Bench", "PUB": "Pull-up Bar",
    "DS": "Dip Station", "LM": "Landmine", "MB": "Medicine Ball", "SB": "Stability Ball",
    "BT": "Balance Trainer", "TRX": "TRX", "PL": "Plate", "BOX": "Box", "TM": "Treadmill",
    "BK": "Bike", "RW": "Rower", "EL": "Elliptical", "SS": "Stair Stepper", "ROPE": "Battle Ropes",
    "FR": "Foam Roller", "AW": "Ab Wheel", "SR": "Squat Rack",
}
LOADS = {"Dumbbell", "Barbell", "EZ-Bar", "Trap Bar", "Kettlebell", "Cable", "Machine",
         "Smith Machine", "Leg Press", "Hack Squat", "Hammer Strength", "Landmine",
         "Medicine Ball", "Plate", "None"}
TYPES = {"W": "Weighted", "B": "Bodyweight", "T": "Timed", "C": "Cardio"}
MECH = {"C": "Compound", "I": "Isolation"}

# RepMin, RepMax, Sets, RestSec, SecPerRep
PROFILES = {
    "H": (6, 10, 4, 150, 3),    # heavy main compound
    "C": (8, 12, 3, 90, 3),     # compound
    "I": (8, 12, 3, 60, 3),     # isolation
    "L": (10, 15, 3, 60, 3),    # light isolation: delts, calves, forearms, hip ab/adduction, rotator cuff
    "A": (12, 20, 3, 45, 2),    # abs / obliques reps
    "B": (8, 15, 3, 60, 2),     # bodyweight compound
    "PU": (5, 10, 3, 90, 3),    # pull-ups, chin-ups, dips
    "X": (5, 8, 4, 120, 2),     # explosive / olympic
    "S": (12, 20, 3, 60, 2),    # swings, slams, conditioning reps
    "T": (30, 60, 3, 45, 1),    # isometric holds
    "M": (30, 60, 2, 15, 1),    # mobility / stretching / foam rolling (seconds)
    "K": (20, 45, 1, 0, 1),     # cardio (minutes)
}


HISTORY = r"""
Lat Pulldown|LAT|BI,UB|CA|CA|1|W|C|C|Pull the bar to your upper chest by driving elbows down, chest tall, no swinging.
EZ-Bar Curl|BI|FA|EZ|EZ|1|W|I|I|Keep elbows pinned at your sides and curl without swinging the torso.
Standing Machine Calf Press|CAL||MA|MA|1|W|I|L|Lower heels to a deep stretch, pause, then rise as high as possible.
Machine Hip Adductor|ADD||MA|MA|1|W|I|L|Squeeze the pads together under control and resist slowly on the way out.
Barbell Bench Press|CH|TRI,FD|BB,BN,SR|BB|1|W|C|H|Retract shoulder blades, lower the bar to mid chest and press up with feet planted.
Machine Hip Abductor|ABD|GL|MA|MA|1|W|I|L|Push the pads outward with your hips, pause, and return slowly.
Dumbbell Fly|CH|FD|DB,BN|DB|2|W|I|I|Keep a soft bend in the elbows and open wide until you feel a chest stretch.
Deadlift|HM|GL,LB,Q|BB|BB|1|W|C|H|Brace hard, keep the bar against your legs and push the floor away with a flat back.
Barbell Hip Thrust|GL|HM|BB,BN|BB|1|W|C|H|Upper back on the bench, drive through heels and lock out hips with a squeeze.
Close-Grip Bench Press|TRI|CH,FD|BB,BN,SR|BB|1|W|C|H|Hands shoulder width, elbows tucked, lower to lower chest and press to lockout.
Leg Press|Q|GL,HM|LP|LP|1|W|C|H|Lower until knees reach about 90 degrees without the lower back lifting off the pad.
Machine Leg Press|Q|GL,HM|LP|LP|1|W|C|H|Control the sled down to a deep knee bend and press through the whole foot.
Barbell Incline Bench Press|CH|FD,TRI|BB,IBN,SR|BB|1|W|C|H|Lower the bar to the upper chest with elbows slightly tucked and press up and back.
Dumbbell Row|LAT|UB,BI|DB,BN|DB|1|W|C|C|Support yourself on the bench and pull the dumbbell to your hip, keeping the back flat.
Seated Back Extension|LB|GL,HM|MA|MA|1|W|I|I|Extend the spine against the pad under control without jerking or hyperextending.
Machine Fly|CH|FD|MA|MA|1|W|I|I|Bring the handles together in a wide arc and squeeze the chest at the middle.
Back Squat|Q|GL,HM,LB|BB,SR|BB|1|W|C|H|Brace, sit down between your heels to at least parallel and drive up with chest tall.
Dumbbell Skullcrusher|TRI||DB,BN|DB|2|W|I|I|Keep upper arms still and lower the dumbbells beside your head, then extend fully.
Cable Rope Tricep Extension|TRI||CA|CA|1|W|I|I|Pin elbows to your sides and push the rope down, spreading the ends at the bottom.
Romanian Deadlift|HM|GL,LB|BB|BB|1|W|C|H|Push hips back with soft knees, bar close to legs, until you feel a hamstring stretch.
Seated Machine Calf Press|CAL||MA|MA|1|W|I|L|Lower heels for a full stretch, pause, and press up onto the balls of your feet.
Side Laterals to Front Raise|SD|FD|DB|DB|2|W|I|L|Raise to the sides to shoulder height, lower, then raise to the front with control.
Barbell Shoulder Press|FD|SD,TRI|BB,SR|BB|1|W|C|H|Squeeze glutes, press the bar overhead in a straight line and finish with head through.
Cable Row|UB|LAT,BI,RD|CA|CA|1|W|C|C|Sit tall and pull the handle to your stomach, squeezing shoulder blades together.
Pull Up|LAT|BI,UB|PUB|NONE|0|B|C|PU|Start from a dead hang and pull your chest toward the bar with elbows driving down.
Barbell Front Raise|FD|SD|BB|BB|1|W|I|L|Raise the bar to eye level with straight arms and lower slowly without leaning back.
Barbell Curl|BI|FA|BB|BB|1|W|I|I|Curl the bar with elbows fixed at your sides and lower it fully under control.
Dumbbell Bicep Curl|BI|FA|DB|DB|2|W|I|I|Curl with palms up and elbows still, squeezing at the top and lowering slowly.
Incline Dumbbell Row|UB|LAT,RD,BI|DB,IBN|DB|2|W|C|C|Lie chest down on the incline bench and row both dumbbells, squeezing shoulder blades.
Lying Hamstrings Curl|HM|CAL|MA|MA|1|W|I|I|Keep hips pressed into the pad and curl heels toward glutes, lowering slowly.
Incline Back Extension|LB|GL,HM|MA,PL|PL|1|W|I|I|Hinge at the hips on the 45 degree bench and rise until body forms a straight line.
Dumbbell Bench Press|CH|TRI,FD|DB,BN|DB|2|W|C|C|Lower the dumbbells to chest level with elbows at 45 degrees and press up together.
Dumbbell Shoulder Press|FD|SD,TRI|DB,BN|DB|2|W|C|C|Seated tall, press the dumbbells overhead without arching the lower back.
Bicycle Crunch|ABS|OBL|MAT|NONE|0|B|I|A|Bring opposite elbow toward knee while the other leg extends, rotating from the ribs.
Stability Ball Hip Bridge|GL|HM|SB,MAT|NONE|0|T|I|T|Heels on the ball, lift hips into a straight line and hold with glutes squeezed.
Front Squat|Q|GL,ABS|BB,SR|BB|1|W|C|H|Keep elbows high and torso upright as you squat deep and drive up.
Ab Crunch Machine|ABS||MA|MA|1|W|I|A|Curl the ribs toward the hips using the abs, not the arms, and return slowly.
Skullcrusher|TRI||EZ,BN|EZ|1|W|I|I|Lower the bar toward your forehead with elbows pointing up, then extend fully.
Dumbbell Lunge|Q|GL,HM|DB|DB|2|W|C|C|Step forward and lower the back knee toward the floor, then push back to start.
Leg Extension|Q||MA|MA|1|W|I|I|Extend the knees fully and squeeze the quads, then lower under control.
Machine Row|UB|LAT,BI,RD|MA|MA|1|W|C|C|Chest on the pad, pull handles back and squeeze shoulder blades together.
Hammer Curls|BI|FA|DB|DB|2|W|I|I|Hold dumbbells with neutral grip and curl without letting elbows drift forward.
Sit Up|ABS||MAT|NONE|0|B|I|A|Curl up vertebra by vertebra to sitting and lower slowly, feet anchored.
Cable Lateral Raise|SD||CA|CA|1|W|I|L|Raise the handle out to the side to shoulder height with a slight elbow bend.
Leg Raise|ABS||MAT|NONE|0|B|I|A|Press the lower back into the floor and raise straight legs, lowering slowly.
Dumbbell Incline Fly|CH|FD|DB,IBN|DB|2|W|I|I|On an incline bench open the arms in a wide arc and squeeze the upper chest.
Exercise Ball Crunch|ABS||SB|NONE|0|B|I|A|Lie back over the ball and crunch the ribs toward the hips without pulling the neck.
Bent Over Barbell Row|UB|LAT,RD,BI|BB|BB|1|W|C|H|Hinge to about 45 degrees with a flat back and row the bar to your lower ribs.
Hack Squat|Q|GL|HSQ|HSQ|1|W|C|H|Back flat on the pad, lower deep with knees tracking over toes and drive up.
Superman|LB|GL,UB|MAT|NONE|0|B|I|B|Lying face down, lift arms, chest and legs together and pause at the top.
Dumbbell Rear Delt Raise|RD|UB|DB|DB|2|W|I|L|Hinge forward and raise the dumbbells out wide, leading with the elbows.
Crunches|ABS||MAT|NONE|0|B|I|A|Curl shoulders off the floor by contracting the abs, keep the chin off the chest.
Barbell Seated Calf Raise|CAL||BB,BN|BB|1|W|I|L|Seated with the padded bar on your knees, raise heels high and lower to a stretch.
Dumbbell Incline Bench Press|CH|FD,TRI|DB,IBN|DB|2|W|C|C|Press the dumbbells up from the upper chest on an incline bench, elbows at 45 degrees.
Push Up|CH|TRI,FD,ABS|BW|NONE|0|B|C|B|Body in a straight line, lower your chest to the floor and press back up.
Leg Pull-In|ABS||MAT|NONE|0|B|I|A|Seated and leaning back, pull knees to chest and extend legs without touching down.
Barbell Decline Bench Press|CH|TRI,FD|BB,DBN,SR|BB|1|W|C|H|Lower the bar to the lower chest with control and press up over the shoulders.
Scissor Kick|ABS||MAT|NONE|0|B|I|A|Lower back flat, legs low, alternate raising and lowering straight legs.
Machine Tricep Dip|TRI|CH|MA|MA|1|W|C|I|Push the handles down to full lockout and control the return.
Cable Pull Through|GL|HM|CA|CA|1|W|C|C|Face away from the cable, hinge back with soft knees and snap hips forward.
Push Press|FD|TRI,Q,SD|BB,SR|BB|1|W|C|X|Dip with the knees then drive the bar overhead explosively and lock out.
Dumbbell Tricep Extension|TRI||DB,BN|DB|1|W|I|I|Seated, hold one dumbbell overhead with both hands and lower behind the head.
Seated Leg Curl|HM||MA|MA|1|W|I|I|Curl the pad down and back, pause, then let it rise slowly.
Stiff-Legged Barbell Good Morning|HM|GL,LB|BB,SR|BB|1|W|C|C|Bar on upper back, legs nearly straight, hinge forward with a flat back.
Cable Crunch|ABS||CA|CA|1|W|I|A|Kneel and crunch the elbows toward the knees, flexing the spine not the hips.
Vertical Knee Raise|ABS||DS|NONE|0|B|I|A|Back against the pad, raise knees to chest and curl the pelvis up.
Cable Rope Overhead Triceps Extension|TRI||CA|CA|1|W|I|I|Facing away, extend the rope overhead with elbows staying close to your head.
Russian Twist|OBL|ABS|DB,MAT|DB|1|W|I|A|Lean back with feet lifted and rotate the dumbbell side to side with your torso.
Upright Row|SD|TRP,FD|BB|BB|1|W|C|I|Pull the bar up along the body to chest height, elbows leading above the hands.
Scissor Crossover Kick|ABS||MAT|NONE|0|B|I|A|Legs low and straight, cross them over each other alternately keeping the back flat.
Plank|ABS|OBL,LB|MAT|NONE|0|T|C|T|Forearms under shoulders, body straight from head to heels, brace and breathe.
Shotgun Row|LAT|UB,BI|CA|CA|1|W|C|I|Row the single handle to your hip while rotating slightly, elbow close to body.
Bench Dip|TRI|CH,FD|BN|NONE|0|B|C|B|Hands on the bench behind you, lower until elbows reach 90 degrees and press up.
Deadlift to Calf Raise|HM|GL,CAL,LB|BB|BB|1|W|C|C|Deadlift to standing, then rise onto your toes before lowering the bar.
Preacher Curl|BI||EZ,PBN|EZ|1|W|I|I|Arms flat on the pad, curl up and lower until arms are almost straight.
Chin Up|LAT|BI,UB|PUB|NONE|0|B|C|PU|Underhand grip, pull your chin over the bar and lower to a full hang.
Burpee|CAR|Q,CH,ABS|BW|NONE|0|B|C|S|Drop to a push up, jump feet in, and jump up with arms overhead.
EZ-Bar Overhead Tricep Extension|TRI||EZ|EZ|1|W|I|I|Hold the bar overhead and lower it behind your head, elbows pointing forward.
Tricep Push Up|TRI|CH,FD|BW|NONE|0|B|C|B|Hands under shoulders, elbows brushing the ribs as you lower and press.
Cable Tricep Pushdown|TRI||CA|CA|1|W|I|I|Keep elbows tucked and push the bar down to full extension.
Good Morning|HM|GL,LB|BB,SR|BB|1|W|C|C|Bar on upper back, soft knees, push hips back until torso is near parallel.
Kettlebell Sumo Squat|Q|ADD,GL|KB|KB|1|W|C|C|Wide stance, toes out, hold the kettlebell and sit straight down between the heels.
Decline Crunch|ABS||DBN|NONE|0|B|I|A|Feet hooked on the decline bench, curl up toward the knees and lower slowly.
Neutral Grip Pull Up|LAT|BI,UB|PUB|NONE|0|B|C|PU|Palms facing each other, pull until your chin clears the handles.
Dumbbell Lateral Raise|SD||DB|DB|2|W|I|L|Raise the dumbbells out to shoulder height leading with the elbows, no swinging.
Dumbbell Romanian Deadlift|HM|GL,LB|DB|DB|2|W|C|C|Slide the dumbbells down the thighs by pushing hips back, keep the back flat.
Machine Shoulder Press|FD|SD,TRI|MA|MA|1|W|C|C|Press the handles overhead to near lockout and lower to shoulder level.
Incline EZ-Bar Curl|BI||EZ,IBN|EZ|1|W|I|I|Chest supported on the incline bench, curl the bar with arms hanging straight down.
Seated Dumbbell Curl|BI|FA|DB,BN|DB|2|W|I|I|Seated upright, curl both dumbbells without leaning back.
Smith Machine Bent Over Row|UB|LAT,BI|SM|SM|1|W|C|C|Hinge forward and row the bar to the lower ribs, keeping the torso still.
Decline Push Up|CH|FD,TRI|BN|NONE|0|B|C|B|Feet on the bench, hands on the floor, lower your chest and press up.
Reverse Barbell Curl|FA|BI|BB|BB|1|W|I|I|Overhand grip, curl the bar keeping wrists straight and elbows fixed.
Oblique Crunch|OBL|ABS|MAT|NONE|0|B|I|A|Lying on your side, crunch the top ribs toward the hip.
Single Arm High Cable Tricep Extension|TRI||CA|CA|1|W|I|I|Facing away from a high pulley, extend one arm forward and overhead.
Barbell Shrug|TRP||BB|BB|1|W|I|L|Lift the shoulders straight up toward the ears, pause and lower slowly.
Dumbbell Kickbacks|TRI||DB|DB|2|W|I|I|Hinge forward, upper arms parallel to the floor, extend elbows fully.
Pulse Back Squat|Q|GL|BB,SR|BB|1|W|C|C|Squat down, pulse up a few inches and back down, then stand up.
Hip Thrust|GL|HM|BN,MAT|NONE|0|B|C|B|Upper back on the bench, drive through heels to full hip lockout and squeeze.
Alternating Superman|LB|GL,UB|MAT|NONE|0|B|I|A|Lying face down, lift opposite arm and leg, pause, and switch sides.
Decline Sit Up|ABS||DBN|NONE|0|B|I|A|Feet secured, sit all the way up from the decline and lower slowly.
Cable One Arm Tricep Side Extension|TRI||CA|CA|1|W|I|I|Pull the handle across and extend the arm out to the side, elbow fixed.
Dumbbell Front Raise|FD||DB|DB|2|W|I|L|Raise the dumbbells in front to eye level with straight arms, lower slowly.
Dumbbell Squat|Q|GL,HM|DB|DB|2|W|C|C|Dumbbells at your sides, squat to parallel with chest up and drive through the feet.
Flutter Kicks|ABS||MAT|NONE|0|B|I|A|Lower back pressed down, kick straight legs up and down in small fast motions.
Decline Russian Twists|OBL|ABS|DB,DBN|DB|1|W|I|A|Sit on the decline bench leaning back and rotate the weight side to side.
Gorilla Rows|UB|LAT,BI|KB|KB|2|W|C|C|Wide stance hinge with both kettlebells on the floor, row one at a time.
Cross Body Hammer Curls|BI|FA|DB|DB|2|W|I|I|Curl each dumbbell across the body toward the opposite shoulder.
Reverse Crunch|ABS||MAT|NONE|0|B|I|A|Curl the hips off the floor bringing knees toward the chest, lower slowly.
Kettlebell Alternating Row|UB|LAT,BI|KB|KB|2|W|C|C|Hinge forward holding two kettlebells and row them one at a time.
Standing Dumbbell Tricep Extension|TRI||DB|DB|1|W|I|I|Hold one dumbbell overhead with both hands and lower behind your head.
Barbell Step Up|Q|GL,HM|BB,BOX,SR|BB|1|W|C|C|Step onto the box driving through the front heel, stand tall, step down slowly.
Concentration Curl|BI||DB,BN|DB|1|W|I|I|Seated, elbow braced on inner thigh, curl the dumbbell and squeeze.
Cable Hip Extension|GL|HM|CA|CA|1|W|I|I|Ankle strap on, kick the leg straight back squeezing the glute without arching.
Standing Dumbbell Shoulder Press|FD|SD,TRI,ABS|DB|DB|2|W|C|C|Standing braced, press the dumbbells overhead without leaning back.
Cable Underhand Tricep Pushdown|TRI||CA|CA|1|W|I|I|Underhand grip, elbows pinned, push the bar down to full extension.
V-Bar Pulldown|LAT|BI,UB|CA|CA|1|W|C|C|Pull the V-handle to your upper chest, leaning back slightly, elbows down.
Dumbbell Bent Over Row|UB|LAT,RD,BI|DB|DB|2|W|C|C|Hinge to 45 degrees with a flat back and row both dumbbells to your hips.
Seated Barbell Shoulder Press|FD|SD,TRI|BB,BN,SR|BB|1|W|C|H|Seated with back supported, press the bar overhead and lower to the chin.
Barbell Back Squat with Deep Partial Squat|Q|GL,HM|BB,SR|BB|1|W|C|C|Squat deep, rise halfway, sink back to the bottom, then stand up.
Barbell Bicep Drag Curl|BI|FA|BB|BB|1|W|I|I|Drag the bar up along your torso by pulling elbows back.
Jackknife Sit-Up|ABS||MAT|NONE|0|B|I|A|Raise arms and legs together to meet over the hips, then lower slowly.
Close-Grip EZ-Bar Curl|BI|FA|EZ|EZ|1|W|I|I|Narrow grip on the EZ bar, curl with elbows fixed and lower slowly.
Balance Trainer Crunch|ABS||BT|NONE|0|B|I|A|Lower back on the dome, crunch up through a full range of motion.
Australian Chin Up|LAT|BI,UB|BB,SR|NONE|0|B|C|B|Hang under a racked bar with underhand grip, body straight, pull chest to the bar.
Sumo Deadlift|GL|Q,ADD,HM|BB|BB|1|W|C|H|Wide stance, hands inside knees, push the floor apart and stand up tall.
Incline Dumbbell Curl|BI||DB,IBN|DB|2|W|I|I|Lie back on an incline bench, arms hanging, curl without moving the elbows.
Dumbbell Glute Bridge|GL|HM|DB,MAT|DB|1|W|I|I|Dumbbell on hips, drive through heels to lift hips and squeeze at the top.
Dumbbell Back Fly|RD|UB|DB|DB|2|W|I|L|Bent over with flat back, open the arms wide and squeeze the rear delts.
Superman with Scaption|LB|UB,RD|MAT|NONE|0|B|I|B|Lying face down, lift chest and legs while raising arms in a Y.
Arnold Dumbbell Press|FD|SD,TRI|DB,BN|DB|2|W|C|C|Start palms facing you and rotate them outward as you press overhead.
Reverse Grip Barbell Bent Over Row|LAT|UB,BI|BB|BB|1|W|C|C|Underhand grip, hinge forward and row the bar to your lower stomach.
Cable One Arm Underhand Tricep Extension|TRI||CA|CA|1|W|I|I|Underhand grip on a single handle, extend the elbow fully at your side.
Single Arm Low Cable Crossover Fly|CH|FD|CA|CA|1|W|I|I|From a low pulley, sweep one arm up and across toward the opposite shoulder.
Cable Wood Chop|OBL|ABS|CA|CA|1|W|C|A|Rotate the torso pulling the handle diagonally across the body, pivoting the back foot.
Superman Hold|LB|GL,UB|MAT|NONE|0|T|I|T|Lift arms, chest and legs off the floor and hold the position.
Dumbbell Wide Curls|BI||DB|DB|2|W|I|I|Curl the dumbbells with arms angled outward, elbows fixed at your sides.
Dumbbell Preacher Curls|BI||DB,PBN|DB|2|W|I|I|Arms on the preacher pad, curl both dumbbells and lower to nearly straight.
Hanging Knee Raise|ABS||PUB|NONE|0|B|I|A|Hang from the bar and raise knees toward chest without swinging.
1/2 Kneeling Shotgun Row|LAT|UB,BI|CA|CA|1|W|C|I|Half kneeling, row the handle to your hip with a slight rotation.
Machine Preacher Curl|BI||MA|MA|1|W|I|I|Arms on the pad, curl the handles up and resist on the way down.
Air Squats|Q|GL|BW|NONE|0|B|C|B|Feet shoulder width, squat to parallel with chest up and stand tall.
Elevated Hip Bridge|GL|HM|BN,MAT|NONE|0|B|I|B|Feet on the bench, drive hips up to a straight line and squeeze.
Barbell Lunge|Q|GL,HM|BB,SR|BB|1|W|C|C|Bar on your back, step forward and lower the back knee, then push back.
Medicine Ball Superman|LB|GL,UB|MB,MAT|MB|1|W|I|B|Holding the ball overhead, lift arms, chest and legs together.
Spider Curls|BI||DB,IBN|DB|2|W|I|I|Chest down on the incline bench, arms hanging, curl and squeeze hard.
Medicine Ball Russian Twist|OBL|ABS|MB,MAT|MB|1|W|I|A|Lean back with feet up and rotate the ball side to side.
Kneeling Squat|GL|HM|BB,SR,MAT|BB|1|W|C|C|Kneel with the bar on your back, sit hips to heels and drive them forward.
Lunge|Q|GL,HM|BW|NONE|0|B|C|B|Step forward and lower the back knee toward the floor, then return.
Cable Crossover Fly|CH|FD|CA|CA|2|W|I|I|Bring the handles together in front of the chest in a hugging arc.
Dumbbell Seated Single Arm Shoulder Press|FD|SD,TRI|DB,BN|DB|1|W|C|C|Seated tall, press one dumbbell overhead without leaning to the side.
Landmine Romanian Deadlift|HM|GL,LB|LM,BB|LM|1|W|C|C|Hold the bar end, push hips back with soft knees and stand up tall.
Single Leg Glute Bridge|GL|HM|MAT|NONE|0|T|I|T|One foot planted, lift hips level and hold with the glute squeezed.
Dead Bug|ABS||MAT|NONE|0|B|I|A|Lower back pressed down, extend opposite arm and leg slowly and return.
Cable Face Pull|RD|UB,TRP|CA|CA|1|W|I|L|Pull the rope toward your face, hands apart and elbows high.
Pause Barbell Decline Bench Press|CH|TRI,FD|BB,DBN,SR|BB|1|W|C|H|Lower to the lower chest, pause motionless, then press up.
Stability Ball Hip Thrust|GL|HM|SB|NONE|0|B|C|B|Upper back on the ball, drive hips up to a tabletop and squeeze.
Landmine Single Leg Romanian Deadlift|HM|GL,LB|LM,BB|LM|1|W|C|C|Hinge on one leg holding the bar end, hips square, back flat.
Single Leg Standing Calf Raise|CAL||BW|NONE|0|B|I|L|Stand on one foot and rise as high as possible, lower slowly.
EZ-Bar Pull Over|LAT|CH,TRI|EZ,BN|EZ|1|W|I|I|Lying on the bench, lower the bar behind your head with slightly bent arms.
Pause Barbell Incline Bench Press|CH|FD,TRI|BB,IBN,SR|BB|1|W|C|H|Lower to the upper chest, pause motionless, then press up.
Dumbbell Squat To Shoulder Press|Q|FD,GL,TRI|DB|DB|2|W|C|C|Squat with dumbbells at shoulders and press them overhead as you stand.
Single Arm Preacher Curl|BI||DB,PBN|DB|1|W|I|I|Arm on the preacher pad, curl the dumbbell and lower until almost straight.
Balance Trainer Squat|Q|GL,ABS|BT|NONE|0|B|C|B|Stand on the dome and squat with control, keeping knees aligned.
Side Leg Raises|ABD|GL|MAT|NONE|0|B|I|A|Lying on your side, raise the top leg straight up and lower slowly.
Smith Machine Close-Grip Bench Press|TRI|CH,FD|SM,BN|SM|1|W|C|C|Narrow grip, elbows tucked, lower to the lower chest and press.
Barbell Pause Curl|BI|FA|BB|BB|1|W|I|I|Curl the bar, pause halfway down for a second, then finish the rep.
Kettlebell Row|LAT|UB,BI|KB|KB|1|W|C|C|Hinge with a flat back and row the kettlebell to your hip.
Incline Barbell Skull Crusher|TRI||BB,IBN|BB|1|W|I|I|On an incline bench lower the bar behind your head and extend fully.
Cable Bicep Curl|BI|FA|CA|CA|1|W|I|I|Curl the bar from the low pulley keeping elbows at your sides.
Incline Hammer Curl|BI|FA|DB,IBN|DB|2|W|I|I|Lie back on an incline bench and curl with neutral grip.
Tuck Crunch|ABS||MAT|NONE|0|B|I|A|Knees tucked, crunch the shoulders up while drawing knees in.
Wide Grip Barbell Curl|BI||BB|BB|1|W|I|I|Grip wider than shoulders and curl with elbows fixed.
Hand Release Push Up|CH|TRI,FD|BW|NONE|0|B|C|B|Lower fully, lift hands off the floor briefly, then press back up.
Overhead Cable Bicep Curl|BI||CA|CA|1|W|I|I|Arms out at shoulder height, curl the handles toward your head.
Cable Rope Hammer Curls|BI|FA|CA|CA|1|W|I|I|Curl the rope with neutral grip, elbows still.
Single Arm Lat Pulldown|LAT|BI|CA|CA|1|W|C|I|Pull one handle down to your shoulder, driving the elbow to the hip.
Single Arm Cable Press|CH|FD,TRI|CA|CA|1|W|C|I|Press the handle forward from the chest while bracing against rotation.
Standing Barbell Calf Raise|CAL||BB,SR|BB|1|W|I|L|Bar on your back, rise onto toes as high as possible and lower slowly.
Dumbbell Shrug|TRP||DB|DB|2|W|I|L|Shrug straight up toward the ears, pause, and lower slowly.
Single Arm Dumbbell Tricep Extension|TRI||DB|DB|1|W|I|I|Hold one dumbbell overhead, lower behind the head and extend fully.
Reverse Dumbbell Curl|FA|BI|DB|DB|2|W|I|I|Palms down, curl the dumbbells with straight wrists.
Wide Grip Lat Pulldown|LAT|UB,BI|CA|CA|1|W|C|C|Wide grip, pull the bar to your upper chest with elbows driving down.
Side Bridge|OBL|ABS|MAT|NONE|0|T|I|T|On one forearm, lift hips into a straight line and hold.
Dumbbell Superman|LB|GL,UB|DB,MAT|DB|2|W|I|I|Holding light dumbbells, lift arms, chest and legs off the floor.
Front Plate Raise|FD||PL|PL|1|W|I|L|Hold the plate at the sides and raise it to eye level with straight arms.
Stability Ball Oblique Crunch|OBL|ABS|SB|NONE|0|B|I|A|Side on the ball with feet braced, crunch the top ribs toward the hip.
Floor Press|CH|TRI,FD|BB,SR|BB|1|W|C|C|Lying on the floor, lower until elbows touch down, pause, and press.
Dumbbell Step Up|Q|GL,HM|DB,BOX|DB|2|W|C|C|Step onto the box driving through the front heel, step down slowly.
Vertical Leg Raise|ABS||DS|NONE|0|B|I|A|Back on the pad, raise straight legs to hip height and lower slowly.
Smith Machine Incline Bench Press|CH|FD,TRI|SM,IBN|SM|1|W|C|C|Lower the bar to the upper chest on an incline and press up.
Balance Trainer Braced Frog Kicks|ABS||BT|NONE|0|B|I|A|Seated on the dome leaning back, extend and tuck the legs together.
Single Leg Leg Extension|Q||MA|MA|1|W|I|I|Extend one knee fully and squeeze the quad, lower slowly.
Pause Front Squat|Q|GL,ABS|BB,SR|BB|1|W|C|H|Squat deep, pause in the bottom without relaxing, then drive up.
Pause Back Squat|Q|GL,HM|BB,SR|BB|1|W|C|H|Squat to depth, pause for a full second, then drive up.
Single Leg Kickback|GL|HM|MAT|NONE|0|B|I|A|On all fours, kick one leg back and up squeezing the glute.
Elbow to Knee Crunch|ABS|OBL|MAT|NONE|0|B|I|A|Crunch up and bring elbow to the opposite knee, alternating sides.
Dumbbell Decline Fly|CH|FD|DB,DBN|DB|2|W|I|I|On a decline bench open the arms wide and bring them back together over the chest.
Landmine Row|UB|LAT,BI|LM,BB|LM|1|W|C|C|Straddle the bar, hinge forward and row the end toward your chest.
Cocoon Crunch|ABS||MAT|NONE|0|B|I|A|From lying extended, pull knees in and arms forward to meet over the hips.
Wide Grip Pull Up|LAT|UB,BI|PUB|NONE|0|B|C|PU|Wide grip, pull your chest toward the bar with elbows driving down.
Forward Lunge with Twist|Q|GL,OBL|DB|DB|1|W|C|C|Lunge forward and rotate the weight over the front leg, then return.
Dual Kettlebell Front Squat|Q|GL,ABS|KB|KB|2|W|C|C|Kettlebells racked at shoulders, squat deep with an upright torso.
Reverse Grip Pull Down|LAT|BI|CA|CA|1|W|C|C|Underhand grip, pull the bar to your chest with elbows tight.
Kettlebell Swing|GL|HM,LB|KB|KB|1|W|C|S|Hike the bell back, then snap the hips forward to float it to chest height.
Dumbbell Hammer Pause Curl|BI|FA|DB|DB|2|W|I|I|Neutral grip curl with a one second pause halfway down.
Machine Bench Press|CH|TRI,FD|MA|MA|1|W|C|C|Press the handles forward to near lockout and return with control.
Smith Machine Bench Press|CH|TRI,FD|SM,BN|SM|1|W|C|C|Lower the bar to mid chest and press up, shoulder blades retracted.
Decline Reverse Crunch|ABS||DBN|NONE|0|B|I|A|Holding the bench, curl hips up toward the chest and lower slowly.
Incline Dumbbell Squeeze Press|CH|TRI,FD|DB,IBN|DB|2|W|C|C|Press the dumbbells together hard and press them up on an incline.
Lateral Cable Tricep Extension|TRI||CA|CA|1|W|I|I|Pull the handle across the body and extend the arm out to the side.
Medicine Ball Single Leg Romanian Deadlift|HM|GL|MB|MB|1|W|C|C|Hinge on one leg holding the ball, keep hips square and back flat.
Pause Bench Press|CH|TRI,FD|BB,BN,SR|BB|1|W|C|H|Lower to the chest, pause motionless, then press up.
Stiff-Legged Deadlift|HM|GL,LB|BB|BB|1|W|C|C|Legs nearly straight, hinge at the hips and lower the bar along the legs.
V-Bar Pull Up|LAT|BI,UB|PUB|NONE|0|B|C|PU|With a V-handle over the bar, pull up and bring your chest to the handle.
Dumbbell Hip Thrust|GL|HM|DB,BN|DB|1|W|C|C|Upper back on the bench, dumbbell on hips, drive up and squeeze.
Dumbbell Drag Pause Curl|BI|FA|DB|DB|2|W|I|I|Drag the dumbbells up the torso, pause at the top, lower slowly.
Pendlay Row|UB|LAT,BI,LB|BB|BB|1|W|C|H|Torso parallel to the floor, row the bar explosively from the floor each rep.
Incline Push Up|CH|TRI,FD|BN|NONE|0|B|C|B|Hands on the bench, body straight, lower chest to the edge and press.
Toe Touchers|ABS||MAT|NONE|0|B|I|A|Legs vertical, reach your hands toward your toes lifting the shoulders.
Trap Bar Deadlift|GL|Q,HM,LB|TB|TB|1|W|C|H|Stand inside the bar, brace, and push the floor away to stand tall.
Dumbbell Sumo Squat|Q|ADD,GL|DB|DB|2|W|C|C|Wide stance, toes out, squat straight down holding the dumbbells.
Clam|ABD|GL|MAT|NONE|0|B|I|A|Lying on your side with knees bent, open the top knee without rolling back.
Inverted Row|UB|LAT,BI,RD|BB,SR|NONE|0|B|C|B|Hang under a racked bar, body straight, pull your chest to the bar.
Waiter Curls|BI|FA|DB|DB|1|W|I|I|Hold one dumbbell flat by the plate end and curl it like a tray.
Machine Rear Delt Fly|RD|UB|MA|MA|1|W|I|L|Facing the pad, sweep the handles back with straight arms.
Medicine Ball Hip Thrusts|GL|HM|MB,BN|MB|1|W|C|C|Upper back on the bench, ball on hips, drive up and squeeze.
Balance Trainer Push Up|CH|TRI,FD,ABS|BT|NONE|0|B|C|B|Hands on the flat side of the trainer, lower chest and press up steadily.
Standing Cable Core Twist|OBL|ABS|CA|CA|1|W|I|A|Arms straight, rotate the handle across the body from the torso.
Cable Front Raise|FD||CA|CA|1|W|I|L|Raise the handle in front to eye level with a straight arm.
Smith Machine Squat|Q|GL,HM|SM|SM|1|W|C|C|Feet slightly forward, squat to depth and drive up through the heels.
Low Cable Chest Fly|CH|FD|CA|CA|2|W|I|I|From low pulleys, sweep the handles up and together at chest height.
Kettlebell Swing American|GL|HM,FD,LB|KB|KB|1|W|C|S|Swing the bell all the way overhead with a powerful hip snap.
Dumbbell Standing Hammer Curl To Front Press|BI|FD,FA|DB|DB|2|W|C|C|Hammer curl to the shoulders, then press the dumbbells forward and up.
Decline Oblique Crunch|OBL|ABS|DBN|NONE|0|B|I|A|On the decline bench, crunch up and rotate toward one knee.
Dumbbell Decline Bench Press|CH|TRI,FD|DB,DBN|DB|2|W|C|C|On a decline bench press the dumbbells up over the lower chest.
Cable Russian Twists|OBL|ABS|CA|CA|1|W|I|A|Seated, rotate the cable handle side to side from the torso.
Dumbbell Upright Row|SD|TRP,FD|DB|DB|2|W|C|I|Pull the dumbbells up to chest height with elbows leading.
Romanian Deadlift to Bent-Over Row|HM|UB,GL,LAT|BB|BB|1|W|C|C|Hinge into an RDL, row the bar to your ribs, then stand up.
Single Arm Landmine Row|LAT|UB,BI|LM,BB|LM|1|W|C|C|Staggered stance, row the bar end to your hip with one arm.
Trap Bar Bent Over Row|UB|LAT,BI|TB|TB|1|W|C|C|Hinge forward inside the trap bar and row it to your torso.
Romanian Deadlift to Shrug|HM|TRP,GL|BB|BB|1|W|C|C|Perform an RDL, stand tall and shrug the shoulders up.
Dumbbell Standing Front Press|FD|TRI,SD|DB|DB|2|W|C|C|Neutral grip at shoulders, press the dumbbells straight up.
EZ-Bar Pause Curl|BI|FA|EZ|EZ|1|W|I|I|Curl the EZ bar with a one second pause halfway down.
Barbell Glute Bridge|GL|HM|BB,MAT|BB|1|W|C|C|Bar over the hips, drive through heels to lift hips and squeeze.
Dumbbell Romanian Deadlift to Shrug|HM|TRP,GL|DB|DB|2|W|C|C|Hinge with the dumbbells, stand tall and shrug at the top.
Opposite Leg Toe Touch|ABS|OBL|MAT|NONE|0|B|I|A|Lying flat, reach one hand to the opposite raised foot, alternating.
Machine Squat|Q|GL|MA|MA|1|W|C|C|Shoulders under the pads, squat to depth and press up through the feet.
Single Arm Kettlebell Deadlift|GL|HM,OBL,Q|KB|KB|1|W|C|C|Hold one kettlebell at your side and deadlift without leaning over.
Single Arm Kettlebell Swing|GL|HM,OBL|KB|KB|1|W|C|S|Swing the bell with one arm driven by a powerful hip snap.
Landmine Sumo Squat|Q|ADD,GL|LM,BB|LM|1|W|C|C|Hold the bar end at your chest, wide stance, squat straight down.
Dumbbell Pause Curl|BI|FA|DB|DB|2|W|I|I|Curl the dumbbells with a one second pause halfway down.
Abdonimal|ABS||MA|MA|1|W|I|A|Crunch the torso forward on the ab machine, moving from the abs only.
EZ Bar PJR Pull Over|TRI|LAT|EZ,BN|EZ|1|W|C|I|Lower the bar to the forehead then behind the head, and pull it back to lockout.
Meadow Landmine Row|LAT|UB,RD|LM,BB|LM|1|W|C|C|Perpendicular to the bar, row the bar end with an overhand grip.
Straight-Arm Pulldown|LAT||CA|CA|1|W|I|I|Keep arms straight and sweep the bar down to your thighs.
Alternating Heel Touch|OBL|ABS|MAT|NONE|0|B|I|A|Shoulders lifted, reach side to side touching each heel.
Balance Trainer Russian Twist|OBL|ABS|BT,DB|DB|1|W|I|A|Sit on the dome leaning back and rotate the dumbbell side to side.
Standing Single Arm Dumbbell Shoulder Press|FD|SD,TRI,OBL|DB|DB|1|W|C|C|Press one dumbbell overhead while bracing to stay upright.
Dumbbell Cuban Shoulder Rotations|RD|UB,SD|DB|DB|2|W|I|L|Raise elbows to shoulder height, rotate forearms up, then press.
Biceps Curl To Shoulder Press|BI|FD,TRI|DB|DB|2|W|C|C|Curl the dumbbells to the shoulders, then press them overhead.
Dumbbell Squeeze Press|CH|TRI|DB,BN|DB|2|W|C|C|Press the dumbbells together hard throughout the bench press.
Zottman Curl|BI|FA|DB|DB|2|W|I|I|Curl palms up, rotate palms down at the top and lower slowly.
Balance Trainer Plank|ABS|OBL|BT|NONE|0|T|C|T|Forearms on the dome, body straight, brace and hold.
Kettlebell Upright Row|SD|TRP|KB|KB|1|W|C|I|Hold the kettlebell with both hands and pull it to chest height.
Tate Press|TRI|CH|DB,BN|DB|2|W|I|I|Lower the dumbbells toward the chest with elbows out, then extend.
Dumbbell Romanian Deadlift to Calf Raise|HM|GL,CAL|DB|DB|2|W|C|C|Perform a dumbbell RDL, stand up and rise onto your toes.
Alternating Dumbbell Bench Press|CH|TRI,FD|DB,BN|DB|2|W|C|C|Press one dumbbell at a time while the other stays locked out.
Assisted Pull Up|LAT|BI,UB|MA|MA|1|W|C|C|Kneel on the pad and pull your chest toward the bar under control.
Behind the Back Cable Bicep Curl|BI||CA|CA|1|W|I|I|Facing away from the cable, curl with the arm slightly behind the body.
Landmine Squat|Q|GL|LM,BB|LM|1|W|C|C|Hold the bar end at your chest and squat deep with an upright torso.
Dumbbell Lateral Raise To Front Raise|SD|FD|DB|DB|2|W|I|L|Raise to the side, lower, then raise to the front with control.
Smith Machine Upright Row|SD|TRP|SM|SM|1|W|C|I|Pull the bar to chest height with elbows leading.
Barbell Behind The Back Shrug|TRP||BB,SR|BB|1|W|I|L|Hold the bar behind your thighs and shrug the shoulders up.
Walking Lunge|Q|GL,HM|BW|NONE|0|B|C|B|Lunge forward step after step, back knee close to the floor.
Landmine Press|FD|CH,TRI|LM,BB|LM|1|W|C|C|Press the bar end up and forward from the shoulder.
Dumbbell Goblet Squat|Q|GL|DB|DB|1|W|C|C|Hold one dumbbell at the chest, sit deep between the heels, chest up.
Dumbbell Floor Press|CH|TRI,FD|DB,MAT|DB|2|W|C|C|Lying on the floor, lower until elbows touch down and press up.
Single Arm Cable Bicep Curl|BI||CA|CA|1|W|I|I|Curl one handle from the low pulley, elbow fixed.
Single Arm Bottoms-up Kettlebell Press|FD|SD,TRI,FA|KB|KB|1|W|C|C|Hold the bell upside down with a tight grip and press it overhead.
Dumbbell Seated Hammer Curl To Front Press|BI|FD,FA|DB,BN|DB|2|W|C|C|Seated, hammer curl the dumbbells and press them overhead.
Behind the Back Cable Lateral Raise|SD||CA|CA|1|W|I|L|With the cable behind you, raise the arm out to shoulder height.
Kettlebell Lunge with Rotation|Q|GL,OBL|KB|KB|1|W|C|C|Lunge forward and rotate the kettlebell over the front knee.
Smith Machine Shrug|TRP||SM|SM|1|W|I|L|Shrug the bar straight up, pause, and lower slowly.
Mountain Climber|ABS|CAR,Q|BW|NONE|0|B|C|A|In a high plank, drive knees to chest one after the other quickly.
Assisted Wide Grip Pull Up|LAT|UB,BI|MA|MA|1|W|C|C|Wide grip on the assisted machine, pull your chest toward the bar.
Seated Dumbbell Front Press|FD|TRI,SD|DB,BN|DB|2|W|C|C|Seated, neutral grip at the shoulders, press straight overhead.
Dumbbell Bulgarian Split Squat|Q|GL,HM|DB,BN|DB|2|W|C|C|Rear foot on the bench, lower the back knee straight down and drive up.
Single Arm Landmine Press|FD|CH,TRI|LM,BB|LM|1|W|C|C|Press the bar end up and forward with one arm, bracing the core.
Kettlebell Single Arm Overhead Lunge|Q|GL,FD,ABS|KB|KB|1|W|C|C|Hold the bell locked out overhead and lunge with control.
Balance Trainer Alternating Lunge|Q|GL|BT|NONE|0|B|C|B|Step onto the dome with alternating legs and lower into a lunge.
Iron Cross|SD|FD|DB|DB|2|W|I|L|Raise the dumbbells to the front, open them to the sides, and lower.
Smith Machine Stiff-Legged Deadlift|HM|GL,LB|SM|SM|1|W|C|C|Legs nearly straight, hinge at the hips keeping the bar close.
Single Leg Glute Bridge and Squeeze|GL|HM|DB,MAT|DB|1|W|I|I|Dumbbell on the hip, bridge up on one leg and squeeze hard at the top.
Leg Raise With Dumbbell Pull Over|ABS|LAT|DB,MAT|DB|1|W|C|A|Raise the legs while pulling the dumbbell over your chest, then extend both.
Seated Dumbbell Rear Delt Raise|RD|UB|DB,BN|DB|2|W|I|L|Seated and leaning forward, raise the dumbbells out wide.
Dumbbell Romanian Deadlift to Bent Over Row|HM|UB,GL,LAT|DB|DB|2|W|C|C|Hinge into an RDL, row the dumbbells, lower them and stand up.
Exercise Ball Pull In|ABS||SB|NONE|0|B|I|A|In a plank with shins on the ball, pull the knees to the chest.
Machine Tricep Extension|TRI||MA|MA|1|W|I|I|Extend the elbows fully against the pads and return slowly.
Seated Single Arm Dumbbell Front Press|FD|TRI,SD|DB,BN|DB|1|W|C|C|Seated, press one dumbbell straight up with a neutral grip.
Single Leg Kettlebell Deadlift|HM|GL|KB|KB|1|W|C|C|Hinge on one leg holding the kettlebell, hips square, back flat.
Mid Cable Crossover Fly|CH|FD|CA|CA|2|W|I|I|From shoulder height pulleys, bring the handles together at the chest.
Plank With Dumbbell Pull Through|ABS|OBL|DB,MAT|DB|1|W|C|A|In a high plank, drag the dumbbell under your body to the other side.
Dumbbell Bent Over Reverse Fly|RD|UB|DB|DB|2|W|I|L|Bent over, raise the dumbbells out wide with slightly bent arms.
Medicine Ball Push Up|CH|TRI,FD|MB|NONE|0|B|C|B|One hand on the ball, lower your chest and press up evenly.
Glute Trainer|GL|HM|MA|MA|1|W|I|I|Drive the platform back with your heel and squeeze the glute.
Balance Trainer Braced Bicycle Kicks|ABS|OBL|BT|NONE|0|B|I|A|Seated on the dome leaning back, alternate extending each leg.
Assisted Dip|TRI|CH,FD|MA|MA|1|W|C|C|Lower until elbows reach 90 degrees and press back to lockout.
Stability Ball Back Extension|LB|GL|SB|NONE|0|B|I|B|Hips on the ball, feet anchored, lift the chest to a straight line.
Dumbbell Drag Curl|BI|FA|DB|DB|2|W|I|I|Drag the dumbbells up the torso by pulling the elbows back.
Smith Machine Overhead Shoulder Press|FD|SD,TRI|SM,BN|SM|1|W|C|C|Seated under the bar, press overhead and lower to chin level.
Cable Rear Delt Fly|RD|UB|CA|CA|2|W|I|L|Cross the cables and pull the handles out wide at shoulder height.
Dumbbell Standing Single Arm Front Press|FD|TRI,OBL|DB|DB|1|W|C|C|Neutral grip, press one dumbbell straight overhead without leaning.
Dumbbell Larson Press|CH|TRI,FD,ABS|DB,BN|DB|2|W|C|C|Bench press the dumbbells with legs extended and feet off the floor.
Standing Dumbbell Calf Raise|CAL||DB|DB|2|W|I|L|Holding the dumbbells, rise onto your toes and lower slowly.
Dumbbell Walking Lunge|Q|GL,HM|DB|DB|2|W|C|C|Hold the dumbbells and lunge forward step after step.
Palms-Up Barbell Wrist Curl|FA||BB,BN|BB|1|W|I|L|Forearms on the bench, curl the bar up with the wrists only.
EZ-Bar Reverse Grip Curl|FA|BI|EZ|EZ|1|W|I|I|Overhand grip on the EZ bar, curl with wrists straight.
Trap Bar Shrugs|TRP||TB|TB|1|W|I|L|Stand in the trap bar and shrug straight up, pause at the top.
Balance Trainer Mountain Climber|ABS|CAR,Q|BT|NONE|0|B|C|A|Hands on the trainer, drive the knees to the chest quickly.
Overhead Barbell Lunge|Q|GL,FD,ABS|BB,SR|BB|1|W|C|C|Hold the bar locked out overhead and lunge with control.
Single Leg Hip Thrust|GL|HM|BN|NONE|0|B|C|B|Upper back on the bench, drive up on one leg to full lockout.
Pike Push Up|FD|TRI,SD|BW|NONE|0|B|C|B|Hips high in an inverted V, lower the head toward the floor and press.
Bodyweight Bulgarian Split Squat|Q|GL,HM|BN|NONE|0|B|C|B|Rear foot on the bench, lower the back knee straight down.
Medicine Ball Glute Bridge|GL|HM|MB,MAT|MB|1|W|I|I|Ball on the hips, drive through the heels and squeeze at the top.
EZ-Bar Reverse Close Grip Curl|FA|BI|EZ|EZ|1|W|I|I|Narrow overhand grip, curl the bar keeping wrists straight.
Cable Wood Chop (Low to High)|OBL|ABS|CA|CA|1|W|C|A|Pull the handle from low to high across the body, rotating the torso.
Calf Press|CAL||LP|LP|1|W|I|L|On the leg press, push the sled with the balls of your feet through full range.
Incline Svend Press|CH|FD|PL,IBN|PL|1|W|I|I|Squeeze the plate between your palms and press it out on an incline.
Single Arm Overhead Press|FD|SD,TRI|DB|DB|1|W|C|C|Press one dumbbell overhead with the core braced.
Assisted Neutral Grip Pull Up|LAT|BI,UB|MA|MA|1|W|C|C|Neutral grip on the assisted machine, pull until the chin clears.
Medicine Ball Leg Crunch|ABS||MB,MAT|MB|1|W|I|A|Ball between the feet, crunch up while pulling the knees in.
Single Arm Cable Crossover|CH|FD|CA|CA|1|W|I|I|Sweep one handle across the chest toward the opposite hip.
Bird Dog Rows|LAT|UB,ABS,GL|DB,BN|DB|1|W|C|C|On the bench in bird dog position, row the dumbbell keeping the hips square.
Balance Trainer Spiderman Push Up|CH|TRI,OBL|BT|NONE|0|B|C|B|Hands on the trainer, bring one knee to the elbow as you lower.
Dumbbell Hang Snatch|GL|Q,FD,TRP|DB|DB|1|W|C|X|From the knees, explode up and punch the dumbbell overhead in one motion.
Machine Bicep Curl|BI||MA|MA|1|W|I|I|Arms on the pad, curl the handles and lower slowly.
Back Extensions|LB|GL,HM|MA|NONE|0|B|I|B|On the hyperextension bench, lower the torso and rise to a straight line.
Standing Elbow to Knee Crunch|ABS|OBL|BW|NONE|0|B|I|A|Standing, drive one knee up to meet the opposite elbow.
Australian Crawl|CAR|ABS,FD,Q|BW|NONE|0|T|C|T|Crawl on hands and feet with knees just off the floor, moving opposite limbs.
Assisted Chin Up|LAT|BI|MA|MA|1|W|C|C|Underhand grip on the assisted machine, pull until the chin clears.
Zottman Preacher Curl|BI|FA|DB,PBN|DB|2|W|I|I|On the preacher pad, curl palms up and lower palms down.
Smith Machine Calf Raise|CAL||SM|SM|1|W|I|L|Under the bar, rise onto the toes as high as possible and lower slowly.
Incline Tricep Push Up|TRI|CH|BN|NONE|0|B|C|B|Hands on the bench, elbows tucked, lower and press back up.
Sumo Squat|Q|ADD,GL|BB,SR|BB|1|W|C|C|Wide stance, toes out, squat straight down with an upright chest.
Smith Machine One-Arm Upright Row|SD|TRP|SM|SM|1|W|C|I|Pull the bar up with one arm, elbow leading above the hand.
TRX Bicep Curl|BI||TRX|NONE|0|B|I|B|Lean back holding the straps and curl your body up toward the hands.
Split Squat|Q|GL,HM|BB,SR|BB|1|W|C|C|Staggered stance, lower the back knee straight down and drive up.
Cable Shrugs|TRP||CA|CA|2|W|I|L|Hold the handles and shrug straight up toward the ears.
Palms-Down Dumbbell Wrist Curl|FA||DB,BN|DB|2|W|I|L|Forearms supported, lift the dumbbells by extending the wrists.
Landmine Squat to Press|Q|FD,GL,TRI|LM,BB|LM|1|W|C|C|Squat with the bar end at your chest and press it up as you stand.
Side Lunge|Q|ADD,GL|BW|NONE|0|B|C|B|Step wide to the side, sit into the hip and keep the other leg straight.
Standing Kettlebell Calf Raise|CAL||KB|KB|2|W|I|L|Holding the kettlebells, rise onto your toes and lower slowly.
Kettlebell Good Morning|HM|GL,LB|KB|KB|1|W|C|C|Hold the bell at your chest and hinge forward with a flat back.
Reverse Grip Bench Press|CH|TRI,FD|BB,BN,SR|BB|1|W|C|C|Underhand grip, lower to the lower chest and press up.
Behind the Neck Push Press|FD|TRI,SD,Q|BB,SR|BB|1|W|C|X|Bar behind the neck, dip and drive it overhead explosively.
Dumbbell Stiff Legged Deadlift|HM|GL,LB|DB|DB|2|W|C|C|Legs nearly straight, lower the dumbbells along the legs.
Mixed Grip Pull Up|LAT|BI,UB|PUB|NONE|0|B|C|PU|One hand over, one under, pull your chest toward the bar.
Balance Trainer Single Leg Hip Thrusters|GL|HM|BT|NONE|0|B|C|B|Shoulders on the dome, drive up on one leg and squeeze.
Exercise Ball Push Up|CH|TRI,ABS|SB|NONE|0|B|C|B|Hands on the ball, keep it steady as you lower and press.
Palms-Up Dumbbell Wrist Curl|FA||DB,BN|DB|2|W|I|L|Forearms supported, curl the dumbbells up with the wrists only.
Smith Machine Single-Leg Split Squat|Q|GL|SM,BN|SM|1|W|C|C|Rear foot elevated under the bar, lower straight down and drive up.
Cable Shoulder Press|FD|SD,TRI|CA|CA|2|W|C|C|Press both handles overhead from the shoulders.
Calf Raise|CAL||BW|NONE|0|B|I|L|Rise onto your toes as high as possible and lower slowly.
Push Up on Knees|CH|TRI,FD|MAT|NONE|0|B|C|B|From your knees, body straight, lower your chest and press.
Medicine Ball Romanian Deadlift|HM|GL|MB|MB|1|W|C|C|Hold the ball and hinge at the hips with a flat back.
Kettlebell Sit Up and Press|ABS|FD|KB,MAT|KB|1|W|C|A|Sit up while pressing the kettlebell overhead, lower with control.
Medicine Ball Lunge|Q|GL|MB|MB|1|W|C|C|Hold the ball at your chest and lunge forward.
Frog Pump|GL||MAT|NONE|0|B|I|A|Soles together, knees out, thrust the hips up and squeeze.
Machine Lateral Raise|SD||MA|MA|1|W|I|L|Raise the pads out to shoulder height and lower slowly.
Dumbbell Pull Over|LAT|CH,TRI|DB,BN|DB|1|W|I|I|Lying on the bench, lower the dumbbell behind the head with slightly bent arms.
Walking|CAR||BW|NONE|0|C|C|[30,60,1,0,1]|Walk at a brisk pace with an upright posture and steady breathing.
Goblet Squat|Q|GL|KB|KB|1|W|C|C|Hold the kettlebell at your chest and squat deep, elbows inside the knees.
Medicine Ball Overhead Lunge|Q|GL,FD,ABS|MB|MB|1|W|C|C|Hold the ball overhead and lunge with control.
Dumbbell Good Morning|HM|GL,LB|DB|DB|1|W|C|C|Hold the dumbbell at your chest and hinge forward with a flat back.
Dumbbell Pullover|LAT|CH,TRI|DB,BN|DB|1|W|I|I|Lying across the bench, lower the dumbbell behind your head and pull back.
Dumbbell Clean|GL|Q,TRP,HM|DB|DB|2|W|C|X|Explode from the hang and catch the dumbbells at the shoulders.
Palms-Down Barbell Wrist Curl|FA||BB,BN|BB|1|W|I|L|Forearms on the bench, lift the bar by extending the wrists.
Hammerstrength Chest Press|CH|TRI,FD|HST|HST|2|W|C|C|Press the handles forward to near lockout and return slowly.
Dip|TRI|CH,FD|DS|NONE|0|B|C|PU|Lower until the elbows reach 90 degrees and press up to lockout.
Balance Trainer Dome Push Ups|CH|TRI,ABS|BT|NONE|0|B|C|B|Hands on the dome, lower your chest and press up steadily.
Weighted Ball Hyperextension|LB|GL,HM|SB,PL|PL|1|W|I|I|Hips on the ball, hold the plate at the chest and lift the torso.
Power Clean|GL|Q,TRP,HM|BB|BB|1|W|C|X|Pull the bar explosively from the floor and catch it on the shoulders.
Dumbbell Hanging Lateral Raise|SD||DB|DB|2|W|I|L|Lean slightly forward and raise the dumbbells out to the side.
Dumbbell V-Sit Cross Jab|OBL|ABS,FD|DB,MAT|DB|2|W|C|A|Balanced in a V-sit, punch the dumbbells across the body alternately.
Kettlebell Halo|FD|SD,TRI,ABS|KB|KB|1|W|I|L|Circle the kettlebell around your head close to the neck, both directions.
Standing Arnold Press|FD|SD,TRI|DB|DB|2|W|C|C|Standing, rotate the palms outward as you press overhead.
Medicine Ball Reverse Lunge|Q|GL|MB|MB|1|W|C|C|Hold the ball at your chest and step back into a lunge.
Cable Crossover Lat Pulldown|LAT|UB|CA|CA|2|W|C|C|Kneel between the pulleys and pull both handles down to your shoulders.
Around the Worlds|CH|FD|DB,BN|DB|2|W|I|I|Lying on the bench, sweep the dumbbells in an arc from hips to overhead.
Stir the Pot|ABS|OBL|SB|NONE|0|B|C|A|Forearms on the ball in a plank, draw small circles without moving the hips.
Cable Upright Row|SD|TRP|CA|CA|1|W|C|I|Pull the bar to chest height with elbows leading.
Oblique Abs  Machine|OBL|ABS|MA|MA|1|W|I|A|Rotate the torso against the resistance and return slowly.
Smith Machine Hip Raise|GL|HM|SM,BN|SM|1|W|C|C|Upper back on the bench, bar over hips, drive up and squeeze.
Overhead Dumbbell Lunge|Q|GL,FD,ABS|DB|DB|2|W|C|C|Hold the dumbbells locked out overhead and lunge with control.
Pulse Lunge|Q|GL|BW|NONE|0|B|C|B|Stay in the lunge and pulse up and down a few inches.
Smith Machine Decline Press|CH|TRI,FD|SM,DBN|SM|1|W|C|C|On a decline bench, lower the bar to the lower chest and press.
Balance Trainer Single Leg Crunches|ABS||BT|NONE|0|B|I|A|Lower back on the dome, one leg extended, crunch up.
Renegade Row|LAT|UB,ABS,CH|DB|DB|2|W|C|C|High plank on the dumbbells, row one at a time without rotating the hips.
Bodyweight Step Up to Deficit Reverse Lunge|Q|GL,HM|BOX|NONE|0|B|C|B|Step up onto the box, then step back down into a deep reverse lunge.
Balance Trainer Incline Push Up|CH|TRI,FD|BT|NONE|0|B|C|B|Hands on the trainer, body straight, lower and press.
Supine Back Stretch|MOB|LB|MAT|NONE|0|T|I|M|Lying on your back, hug the knees toward your chest and relax.
Stability Ball Leg Curl|HM|GL|SB,MAT|NONE|0|B|I|B|Hips lifted, roll the ball toward you with your heels and back out.
Power Clean and Press|GL|FD,Q,TRP|BB|BB|1|W|C|X|Clean the bar to the shoulders, then press it overhead.
Burpee High Jump|CAR|Q,CH,GL|BW|NONE|0|B|C|S|Perform a burpee and finish with a maximal vertical jump.
Smith Machine Glute Bridge|GL|HM|SM,MAT|SM|1|W|C|C|On the floor under the bar, drive the hips up and squeeze.
Alternating Medicine Ball Push Up|CH|TRI,FD|MB|NONE|0|B|C|B|Push up with one hand on the ball, roll it across and switch.
Elevated Platform Deadlift|HM|GL,LB,Q|BB,BOX|BB|1|W|C|C|Stand on the platform and deadlift from a deficit with a flat back.
Medicine Ball Curtsy Lunge|GL|Q,ADD|MB|MB|1|W|C|C|Hold the ball and step back diagonally behind the front leg.
Dumbbell Curtsy Lunge|GL|Q,ADD|DB|DB|2|W|C|C|Step back diagonally behind the front leg and lower the back knee.
Dumbbell Underhand Front Raise|FD|BI|DB|DB|2|W|I|L|Palms up, raise the dumbbells to eye level with straight arms.
Dumbbell Calf Raise to Shrug|CAL|TRP|DB|DB|2|W|C|L|Rise onto your toes and shrug the shoulders at the top.
Kettlebell Sumo High Pull|TRP|GL,SD,Q|KB|KB|1|W|C|C|Wide stance, drive up and pull the bell to chest height, elbows high.
Barbell Curtsy Lunge|GL|Q,ADD|BB,SR|BB|1|W|C|C|Bar on your back, step back diagonally behind the front leg.
Bird Dog|LB|GL,ABS|MAT|NONE|0|B|C|A|On all fours, extend opposite arm and leg without rotating the hips.
Prone Flutter Kicks|LB|GL,HM|MAT|NONE|0|T|I|T|Lying face down, lift the legs and flutter them in small kicks.
Cable Row with Squat|UB|LAT,Q,GL|CA|CA|1|W|C|C|Squat down holding the handle, stand and row it to your stomach.
Seated Dumbbell One-Leg Calf Raise|CAL||DB,BN|DB|1|W|I|L|Seated with the dumbbell on one knee, raise the heel high.
Tuck Jump|Q|CAR,GL,CAL|BW|NONE|0|B|C|S|Jump explosively and pull the knees to the chest, land softly.
Cat Cow|MOB|LB|MAT|NONE|0|T|I|M|On all fours, alternate arching and rounding the spine slowly with the breath.
Stability Ball Hyperextension|LB|GL|SB|NONE|0|B|I|B|Hips on the ball, feet anchored, lift the chest to a straight line.
Jump Squat|Q|GL,CAL|BW|NONE|0|B|C|S|Squat down and jump explosively, landing softly into the next rep.
Medicine Ball Side Lunge|Q|ADD,GL|MB|MB|1|W|C|C|Hold the ball and step wide to the side, sitting into the hip.
Svend Press|CH|FD|PL|PL|1|W|I|I|Squeeze the plate between your palms and press it straight out.
Balance Trainer Goblet Squat|Q|GL,ABS|BT,DB|DB|1|W|C|C|On the dome, hold a dumbbell at the chest and squat with control.
Cable Wrist Curl|FA||CA|CA|1|W|I|L|Curl the bar from the low pulley using the wrists only.
Child's Pose|MOB|LB,LAT|MAT|NONE|0|T|I|M|Sit back onto your heels with arms extended and breathe deeply.
Dead Hang|FA|LAT|PUB|NONE|0|T|I|T|Hang from the bar with straight arms and relaxed shoulders.
Cable Shoulder External Rotation|RD|UB|CA|CA|1|W|I|L|Elbow at your side, rotate the forearm outward against the cable.
Standing Oblique Crunch|OBL|ABS|DB|DB|1|W|I|A|Holding a dumbbell at one side, bend sideways and return.
Single Arm Floor Press|CH|TRI,OBL|DB,MAT|DB|1|W|C|C|On the floor, press one dumbbell up without rolling the torso.
Dumbbell No Money Curls|RD|UB|DB|DB|2|W|I|L|Elbows at your sides, rotate the dumbbells outward and squeeze the back.
Kettlebell Overhead Press|FD|SD,TRI|KB|KB|2|W|C|C|Press the kettlebells overhead from the rack with a braced core.
Smith Machine Behind the Back Shrug|TRP||SM|SM|1|W|I|L|Hold the bar behind you and shrug straight up.
Landmine Core Rotation|OBL|ABS,FD|LM,BB|LM|1|W|C|A|Arms straight, swing the bar end from hip to hip by rotating the torso.
Hammerstrength High Row|UB|LAT,BI|HST|HST|2|W|C|C|Pull the handles down and back, driving the elbows to your sides.
Dumbbell Side Bend|OBL||DB|DB|1|W|I|A|Hold one dumbbell at your side and bend sideways, then return.
Seated Dumbbell Calf Raise|CAL||DB,BN|DB|2|W|I|L|Seated with dumbbells on your knees, raise the heels high.
Walkout to Push Up|CH|ABS,FD,HM|BW|NONE|0|B|C|B|Walk the hands out to a plank, do a push up and walk back.
Rotation Push Up|CH|OBL,TRI,FD|BW|NONE|0|B|C|B|After each push up rotate into a side plank, arm reaching up.
Weighted Wall Sit|Q|GL|PL|PL|1|T|I|T|Back against the wall, thighs parallel, hold the plate on your lap.
Romanian Deadlift to High Pull|HM|TRP,GL,SD|BB|BB|1|W|C|C|Perform an RDL and pull the bar to chest height as you stand.
Dumbbell Thruster|Q|FD,GL,TRI|DB|DB|2|W|C|C|Squat with the dumbbells at your shoulders and drive them overhead.
Clean|GL|Q,TRP,HM|BB|BB|1|W|C|X|Pull the bar explosively and drop under to catch it in a front squat.
Rack Pulls|LB|GL,TRP,HM|BB,SR|BB|1|W|C|H|Pull the bar from knee height in the rack to lockout with a flat back.
Dumbbell Snatch|GL|Q,FD,TRP|DB|DB|1|W|C|X|Explode from the floor and punch one dumbbell overhead in one motion.
Hanging Leg Raise|ABS||PUB|NONE|0|B|I|A|Hang from the bar and raise straight legs to hip height without swinging.
Balance Trainer Wide Pushups|CH|TRI,FD|BT|NONE|0|B|C|B|Wide hands on the trainer, lower your chest and press.
Cross Body Mountain Climber|OBL|ABS,CAR|BW|NONE|0|B|C|A|In a plank, drive each knee toward the opposite elbow.
Diamond Push Up|TRI|CH,FD|BW|NONE|0|B|C|B|Hands together under the chest forming a diamond, lower and press.
Single Dumbbell Sumo Squat|Q|ADD,GL|DB|DB|1|W|C|C|Hold one dumbbell between the legs and squat straight down.
Cable Double Bicep Curl|BI||CA|CA|2|W|I|I|Arms out at shoulder height, curl both handles toward your head.
Elbows Out Bent Over Dumbbell Row|UB|RD,LAT|DB|DB|2|W|C|C|Hinge forward and row with elbows flared wide toward the shoulders.
Dumbbell Halo To Oblique Crunch|OBL|ABS,FD|DB|DB|1|W|C|A|Circle the dumbbell around your head, then crunch knee to elbow.
TRX Squat|Q|GL|TRX|NONE|0|B|C|B|Holding the straps, sit back into a deep squat and stand.
Single Arm Overhead Dumbbell Lunge|Q|GL,FD,OBL|DB|DB|1|W|C|C|Hold one dumbbell locked out overhead and lunge.
Balance Trainer Lying Toe Taps|ABS||BT|NONE|0|B|I|A|Lower back on the dome, lower alternate toes to the floor.
Balance Trainer Curtsy Lunge|GL|Q,ADD|BT|NONE|0|B|C|B|One foot on the dome, step back diagonally into a curtsy lunge.
Balance Trainer Knee Up Squats|Q|GL,ABS|BT|NONE|0|B|C|B|Squat on the dome, stand and drive one knee up.
Cobra Triceps Extension|TRI|CH|MAT|NONE|0|B|I|B|Lying face down, push up through the hands extending the elbows.
Stability Ball Bicycle Crunch|ABS|OBL|SB|NONE|0|B|I|A|Lying on the ball, bring opposite elbow toward knee alternately.
Balance Trainer Side Star Plank|OBL|ABD|BT|NONE|0|B|C|A|Side plank with a hand on the dome, raise the top leg and arm.
Reverse Lunge|Q|GL,HM|BW|NONE|0|B|C|B|Step back and lower the back knee toward the floor, then return.
Elevated Platform Barbell Romanian Deadlift|HM|GL,LB|BB,BOX|BB|1|W|C|C|Stand on the platform and hinge deeper than usual with a flat back.
Olympic Squat|Q|GL,HM|BB,SR|BB|1|W|C|H|High bar on the traps, squat deep with an upright torso.
Cable Crossover Incline Bench Fly|CH|FD|CA,IBN|CA|2|W|I|I|On an incline bench between the pulleys, bring handles together over the chest.
Lower Back Stretch|MOB|LB|MAT|NONE|0|T|I|M|Gently round or twist the lower back and breathe into the stretch.
Cable Shoulder External Rotation at 90°|RD|UB|CA|CA|1|W|I|L|Upper arm at shoulder height, rotate the forearm up and back.
TRX Tricep Extension|TRI||TRX|NONE|0|B|I|B|Lean into the straps and extend the elbows to push your body back.
TRX Calf Raise|CAL||TRX|NONE|0|B|I|L|Hold the straps for balance and rise high onto your toes.
High Plank Arm Reach|ABS|OBL,FD|BW|NONE|0|B|C|A|In a high plank, reach one arm forward without shifting the hips.
Tricep Stretch|MOB|TRI|BW|NONE|0|T|I|M|Reach one hand down your back and gently push the elbow with the other.
T-Bar Row|UB|LAT,BI|LM,BB|LM|1|W|C|C|Straddle the bar, hinge forward and row the handle to your chest.
Step Up|Q|GL|BOX|NONE|0|B|C|B|Step onto the box driving through the front heel and step down slowly.
Chest Dip|CH|TRI,FD|DS|NONE|0|B|C|PU|Lean forward and lower until a chest stretch, then press up.
Hammerstrength Iso Row|LAT|UB,BI|HST|HST|2|W|C|C|Chest on the pad, row the handles back and squeeze.
Landmine Press and Catch|FD|CH,TRI|LM,BB|LM|1|W|C|X|Explosively press the bar end, release, catch, and absorb with control.
TRX Row|UB|LAT,BI|TRX|NONE|0|B|C|B|Lean back with straight body and pull your chest to the handles.
Wall Pectoral Stretch|MOB|CH|BW|NONE|0|T|I|M|Forearm on the wall, rotate the body away until you feel a chest stretch.
Standing Hip Adduction|ADD||BW|NONE|0|B|I|L|Standing tall, sweep one leg across the body and back.
Static Lunge|Q|GL|BW|NONE|0|T|C|T|Hold the bottom of a lunge with the back knee just off the floor.
Seated Figure Four|MOB|GL|BW|NONE|0|T|I|M|Seated, cross one ankle over the opposite knee and lean forward gently.
Power Clean Thruster|Q|GL,FD,TRP|BB|BB|1|W|C|X|Power clean the bar, front squat and drive it overhead.
Hang Power Clean|GL|Q,TRP,HM|BB|BB|1|W|C|X|From mid thigh, explode up and catch the bar high on the shoulders.
Toes to Bar|ABS|LAT|PUB|NONE|0|B|C|A|Hang from the bar and lift your toes to touch it with control.
Balance Trainer Reverse Hyperextension|GL|LB,HM|BT|NONE|0|B|I|B|Hips on the dome, lift the legs behind you to body height.
Balance Trainer Burpee|CAR|CH,Q,ABS|BT|NONE|0|B|C|S|Holding the trainer, drop to a plank, jump in and press it overhead.
Balance Trainer Rear Lunge Kicks|Q|GL|BT|NONE|0|B|C|B|Lunge back off the dome, then drive up into a front kick.
Hang Clean|GL|Q,TRP,HM|BB|BB|1|W|C|X|From the hang, explode up and drop under to a front squat catch.
Kettlebell Hang Clean|GL|Q,TRP|KB|KB|2|W|C|X|From the hang, snap the hips and rack the kettlebells at the shoulders.
Straight Leg Kickback|GL|HM|MAT|NONE|0|B|I|A|On all fours, lift a straight leg back and up, squeezing the glute.
Barbell Ab Rollout|ABS|LAT|BB,MAT|NONE|0|B|C|A|Kneeling, roll the bar forward as far as you can without sagging.
Box Front Squat|Q|GL|BB,SR,BOX|BB|1|W|C|C|Front squat down to sit briefly on the box, then drive up.
Single Arm Reverse Dumbbell Curl|FA|BI|DB|DB|1|W|I|I|Palm down, curl one dumbbell with a straight wrist.
Alternating Single Arm Kettlebell Swing|GL|HM,OBL|KB|KB|1|W|C|S|Swing the bell and switch hands at the top of each rep.
Overhead Weighted Sit Up|ABS|FD|PL,MAT|PL|1|W|I|A|Hold the plate overhead and sit all the way up.
Kettlebell Racked Reverse Lunge|Q|GL,ABS|KB|KB|1|W|C|C|Hold the kettlebell racked at the shoulder and step back into a lunge.
Dumbbell Deficit Reverse Lunge|Q|GL,HM|DB,BOX|DB|2|W|C|C|Stand on a low platform and step back into a deep lunge.
Decline Overhead Weighted Sit Up|ABS|FD|PL,DBN|PL|1|W|I|A|On the decline bench, hold the plate overhead and sit up.
Balance Trainer Leg Crossover Planks|ABS|OBL|BT|NONE|0|B|C|A|In a plank on the trainer, cross one leg under to the other side.
Elliptical|CAR|Q,GL|EL|NONE|0|C|C|K|Keep an upright posture and steady cadence, pushing through the heels.
Cable Crossover Flat Bench Fly|CH|FD|CA,BN|CA|2|W|I|I|On a flat bench between the pulleys, bring handles together over the chest.
Dumbbell Punches|FD|OBL,CAR|DB|DB|2|W|C|S|Holding light dumbbells, punch forward quickly while rotating the torso.
Pause Barbell Lunge|Q|GL,HM|BB,SR|BB|1|W|C|C|Lunge down, pause one second at the bottom, then drive back up.
Balance Trainer Overhead Weighted Crunch|ABS||BT,DB|DB|1|W|I|A|Lying on the dome holding a dumbbell overhead, crunch up.
Cable Shoulder Internal Rotation at 90°|FD|CH|CA|CA|1|W|I|L|Upper arm at shoulder height, rotate the forearm forward and down.
Balance Trainer Rear Glute Raises|GL|HM|BT|NONE|0|B|I|A|Knees on the dome, kick one leg back and up squeezing the glute.
Underhand Rear Delt Raise|RD|UB|DB|DB|2|W|I|L|Bent over with palms forward, raise the dumbbells out wide.
V-Up|ABS||MAT|NONE|0|B|I|A|Lift straight arms and legs together to meet above the hips.
Balance Trainer Shoulder Tap Planks|ABS|OBL,FD|BT|NONE|0|B|C|A|High plank on the trainer, tap each shoulder without rocking.
Plank Shoulder Taps|ABS|OBL,FD|BW|NONE|0|B|C|A|High plank, tap each shoulder with the opposite hand keeping hips still.
Incline Cable Chest Press|CH|FD,TRI|CA,IBN|CA|2|W|C|C|On an incline bench between the pulleys, press the handles up.
Windmill|OBL|HM,FD|BW|NONE|0|B|C|A|One arm overhead, hinge sideways reaching the other hand to the foot.
Freemotion Shoulder Press|FD|SD,TRI|MA|MA|2|W|C|C|Press the handles overhead from the shoulders with control.
Cable Chest Press|CH|FD,TRI|CA|CA|2|W|C|C|Standing between the pulleys, press both handles forward together.
Hammerstrength Decline Chest Press|CH|TRI,FD|HST|HST|2|W|C|C|Press the handles out and down toward the lower chest line.
Hammerstrength Incline Chest Press|CH|FD,TRI|HST|HST|2|W|C|C|Press the handles up and forward along the incline path.
TRX Glute Bridge|GL|HM|TRX,MAT|NONE|0|B|I|B|Heels in the straps, lift the hips into a straight line and squeeze.
Standing Hip Abduction|ABD|GL|BW|NONE|0|B|I|L|Standing tall, lift one leg out to the side without leaning.
Battle Ropes Outside Spiral|CAR|FD,ABS|ROPE|NONE|0|T|C|[20,40,4,60,1]|Make continuous outward circles with both ropes, staying in a half squat.
Battle Ropes Lateral Whip|CAR|OBL,FD|ROPE|NONE|0|T|C|[20,40,4,60,1]|Whip the ropes side to side across the floor, rotating from the core.
Double Dumbbell Power Snatch|GL|Q,FD,TRP|DB|DB|2|W|C|X|Explode up and punch both dumbbells overhead in one motion.
Dumbbell Romanian Deadlift to High Pull|HM|TRP,GL,SD|DB|DB|2|W|C|C|Perform a dumbbell RDL and pull to chest height as you stand.
Downward Dog Push Up|FD|TRI,CH|BW|NONE|0|B|C|B|From downward dog, lower into a push up and push back to the V.
Prone W's|RD|UB,TRP|MAT|NONE|0|B|I|L|Lying face down, squeeze the shoulder blades and lift arms in a W.
Single-Leg Glute Bridge with External Rotation|GL|ABD,HM|MAT|NONE|0|B|I|B|Bridge on one leg and rotate the free knee outward at the top.
Medicine Ball Slam|ABS|LAT,FD,CAR|MB|MB|1|W|C|S|Lift the ball overhead and slam it into the floor with full force.
Standing Leg Side Hold|ABD|GL|BW|NONE|0|T|I|T|Standing tall, hold one leg out to the side without leaning.
Rowing|CAR|UB,Q,LAT|RW|NONE|0|C|C|[15,30,1,0,1]|Drive with the legs first, then lean back and pull to the lower ribs.
Stair Stepper|CAR|Q,GL,CAL|SS|NONE|0|C|C|K|Stand tall, step through the whole foot and avoid leaning on the rails.
Cycling - Stationary|CAR|Q,GL|BK|NONE|0|C|C|K|Keep a steady cadence with the saddle at hip height.
Pallof Press|OBL|ABS|CA|CA|1|W|I|A|Side on to the cable, press the handle straight out and resist rotation.
Cable Shoulder Internal Rotation|FD|CH|CA|CA|1|W|I|L|Elbow at your side, rotate the forearm inward across the body.
Wall Slide Stretch|MOB|UB,RD|BW|NONE|0|T|I|M|Back and arms against the wall, slide the arms up and down slowly.
Hanging Oblique Knee Raise|OBL|ABS|PUB|NONE|0|B|I|A|Hang from the bar and raise the knees toward one side, alternating.
Bench T-Spine Stretch|MOB|LAT,UB|BN|NONE|0|T|I|M|Kneel with elbows on the bench and sink the chest down.
Wrist Extension Stretch|MOB|FA|BW|NONE|0|T|I|M|Arm straight, gently pull the fingers back toward you.
Cable Hip Adduction|ADD||CA|CA|1|W|I|L|Ankle strap on, sweep the leg across the body against the cable.
Cable Hip Abduction|ABD|GL|CA|CA|1|W|I|L|Ankle strap on, sweep the leg out to the side against the cable.
Downward Dog|MOB|HM,CAL|MAT|NONE|0|T|I|M|Hips high, heels pressing toward the floor, lengthen the spine.
Squat with Rotation|MOB|Q,OBL|BW|NONE|0|T|I|M|Hold a deep squat and rotate one arm up toward the ceiling, alternating.
Standing Forward Bend|MOB|HM|BW|NONE|0|T|I|M|Hinge forward with soft knees and let the torso hang relaxed.
Dumbbell Hang Power Clean|GL|Q,TRP|DB|DB|2|W|C|X|From the hang, snap the hips and catch the dumbbells at the shoulders.
Kettlebell Thruster|Q|FD,GL,TRI|KB|KB|2|W|C|C|Squat with the bells racked and drive them overhead as you stand.
Cable Preacher Curl|BI||CA,PBN|CA|1|W|I|I|Arms on the preacher pad, curl the cable bar and lower slowly.
Kettlebell Power Clean|GL|Q,TRP|KB|KB|2|W|C|X|Pull the kettlebells explosively from the floor to the rack position.
Dumbbell Overhead Kneel to Stand|Q|GL,FD,ABS|DB,MAT|DB|2|W|C|C|Hold the dumbbells overhead, kneel down one leg at a time and stand back up.
Stomach Vacuum|ABS||BW|NONE|0|T|I|T|Exhale fully and draw the belly button in toward the spine and hold.
Standing Splits|MOB|HM|BW|NONE|0|T|I|M|Fold forward and lift one leg straight up behind you.
Single Leg Romanian Deadlift|HM|GL,LB|DB|DB|2|W|C|C|Hinge on one leg with a dumbbell in each hand, hips square.
Box Jump|Q|GL,CAL|BOX|NONE|0|B|C|[5,8,3,90,2]|Swing the arms, jump onto the box landing softly, and step down.
Cycling|CAR|Q,GL|BK|NONE|0|C|C|[30,90,1,0,1]|Ride at a steady effort, keeping the cadence smooth.
Foam Roll Hamstrings|MOB|HM|FR|NONE|0|T|I|M|Roll slowly from knee to glute, pausing on tender spots.
Foam Roll Quadriceps|MOB|Q|FR|NONE|0|T|I|M|Face down on the roller, roll slowly from hip to knee.
Foam Roll Chest|MOB|CH|FR|NONE|0|T|I|M|Roll the chest muscle near the armpit slowly with the arm out.
"""

ADDED = r"""
Dumbbell Floor Fly|CH|FD|DB,MAT|DB|2|W|I|I|Lying on the floor, open the arms until the elbows touch down, then squeeze up.
Close-Grip Dumbbell Floor Press|TRI|CH,FD|DB,MAT|DB|2|W|C|C|Dumbbells touching with neutral grip, elbows tucked, press up from the floor.
Wide Grip Push Up|CH|FD,TRI|BW|NONE|0|B|C|B|Hands wider than the shoulders, lower the chest to the floor and press.
Archer Push Up|CH|TRI,FD|BW|NONE|0|B|C|B|Wide hands, shift onto one arm as you lower while the other stays straight.
Dumbbell Deficit Push Up|CH|TRI,FD|DB|NONE|0|B|C|B|Hands on the dumbbell handles, lower the chest below hand level and press.
Pseudo Planche Push Up|FD|CH,TRI|BW|NONE|0|B|C|B|Hands by the lower ribs, lean the shoulders forward past the hands and push up.
Floor Dumbbell Pullover|LAT|CH,TRI|DB,MAT|DB|1|W|I|I|Lying on the floor, lower one dumbbell behind your head with soft elbows and pull back.
Tripod Dumbbell Row|LAT|UB,BI|DB|DB|1|W|C|C|Hand on your front knee, flat back, row the dumbbell to your hip.
Dumbbell Underhand Bent Over Row|LAT|UB,BI|DB|DB|2|W|C|C|Palms forward, hinge to 45 degrees and row the dumbbells to your hips.
Prone Y Raise|TRP|RD,UB|MAT|NONE|0|B|I|L|Lying face down, raise straight arms in a Y with thumbs up and pause.
Prone T Raise|RD|UB,TRP|MAT|NONE|0|B|I|L|Lying face down, raise straight arms out to the sides and squeeze.
Reverse Snow Angel|UB|RD,LB|MAT|NONE|0|B|I|L|Face down with arms lifted, sweep them from hips to overhead and back.
Dumbbell Deadlift|GL|HM,Q,LB|DB|DB|2|W|C|C|Dumbbells beside the feet, brace and stand up with a flat back.
Dumbbell Sumo Deadlift|GL|ADD,HM,Q|DB|DB|1|W|C|C|Wide stance, one heavy dumbbell between the feet, push the floor apart to stand.
Farmer's Carry|FA|TRP,ABS|DB|DB|2|T|C|[30,60,3,60,1]|Hold heavy dumbbells at your sides and walk tall with short quick steps.
Suitcase Carry|OBL|FA,TRP|DB|DB|1|T|C|[30,60,3,60,1]|Carry one heavy dumbbell at your side without leaning, switch sides each set.
Dumbbell Overhead Carry|FD|TRP,ABS|DB|DB|1|T|C|[30,45,3,60,1]|Lock one dumbbell out overhead, ribs down, and walk slowly.
Lu Raise|SD|FD,TRP|DB|DB|2|W|I|L|With light dumbbells, raise straight arms out and up all the way overhead.
Dumbbell Z Press|FD|SD,TRI,ABS|DB,MAT|DB|2|W|C|C|Seated on the floor with legs straight, press the dumbbells overhead without leaning back.
Dumbbell Push Press|FD|TRI,Q,SD|DB|DB|2|W|C|C|Dip with the knees and drive the dumbbells overhead explosively.
Side-Lying Dumbbell External Rotation|RD|UB|DB,MAT|DB|1|W|I|L|Lying on your side, elbow on the hip, rotate the dumbbell up slowly.
Dumbbell Scaption|SD|FD,TRP|DB|DB|2|W|I|L|Thumbs up, raise the dumbbells to shoulder height at 30 degrees in front of the body.
Dumbbell 21s|BI|FA|DB|DB|2|W|I|[21,21,3,60,2]|Do 7 bottom half reps, 7 top half reps, then 7 full curls.
Dumbbell Floor Skullcrusher|TRI||DB,MAT|DB|2|W|I|I|Lying on the floor, lower the dumbbells beside your head and extend fully.
Dumbbell Floor Crossbody Tricep Extension|TRI||DB,MAT|DB|1|W|I|I|Lying down, lower one dumbbell toward the opposite shoulder and extend.
Dumbbell Pronation Supination|FA||DB|DB|1|W|I|L|Hold one end of the dumbbell and rotate the forearm slowly palm up to palm down.
Dumbbell Front Squat|Q|GL,ABS|DB|DB|2|W|C|C|Dumbbells resting on your shoulders, elbows high, squat deep and upright.
Cossack Squat|ADD|Q,GL|BW|NONE|0|B|C|B|Wide stance, sit deep onto one leg while the other stays straight, toes up.
Skater Squat|Q|GL|BW|NONE|0|B|C|B|On one leg, lower the back knee to the floor behind you and stand back up.
Prone Dumbbell Leg Curl|HM||DB,MAT|DB|1|W|I|I|Lying face down, dumbbell between your feet, curl the heels to the glutes.
Glute Bridge Walkout|HM|GL|MAT|NONE|0|B|I|B|From a high bridge, walk the heels out and back while keeping the hips up.
Dumbbell B-Stance Romanian Deadlift|HM|GL|DB|DB|2|W|C|C|Back foot on its toes for balance, hinge mostly on the front leg.
Glute Bridge March|GL|HM,ABS|MAT|NONE|0|B|I|A|Hold a high bridge and lift one knee at a time without dropping the hips.
Fire Hydrant|ABD|GL|MAT|NONE|0|B|I|A|On all fours, lift the bent knee out to the side without shifting the weight.
Side-Lying Hip Adduction|ADD||MAT|NONE|0|B|I|L|Lying on your side, top leg crossed in front, lift the bottom leg up.
Isometric Calf Raise Hold|CAL||DB|DB|2|T|I|T|Holding the dumbbells, rise onto your toes and hold the top position.
Pogo Hops|CAL|CAR|BW|NONE|0|B|I|[20,30,3,60,1]|Bounce quickly on the balls of your feet with stiff ankles and minimal knee bend.
Hollow Body Hold|ABS||MAT|NONE|0|T|I|T|Lower back pressed down, arms and legs extended just off the floor, hold.
Hollow Body Rock|ABS||MAT|NONE|0|B|I|A|In a hollow hold, rock back and forth as one rigid piece.
Dumbbell Dead Bug|ABS||DB,MAT|DB|1|W|I|A|Hold a dumbbell over your chest and lower opposite arm and leg slowly.
Dumbbell Crunch|ABS||DB,MAT|DB|1|W|I|A|Hold a dumbbell on your chest and curl the shoulders off the floor.
Side Plank Hip Dip|OBL|ABS|MAT|NONE|0|B|I|A|In a side plank, lower the hip toward the floor and lift it back up.
Side Plank with Rotation|OBL|ABS,FD|MAT|NONE|0|B|C|A|In a side plank, thread the top arm under the body and rotate back open.
Bear Plank Hold|ABS|FD,Q|MAT|NONE|0|T|C|T|On hands and toes, knees an inch off the floor, back flat, hold.
Dumbbell Wood Chop|OBL|ABS,FD|DB|DB|1|W|C|A|Hold one dumbbell with both hands and chop diagonally from high to low.
Plank Up-Down|ABS|TRI,FD|MAT|NONE|0|B|C|A|From a forearm plank, push up to a high plank one arm at a time and back.
Lying Windshield Wipers|OBL|ABS|MAT|NONE|0|B|I|A|Arms out wide, lower bent knees side to side keeping the shoulders down.
Oblique V-Up|OBL|ABS|MAT|NONE|0|B|I|A|Lying on your side, lift the top arm and both legs together.
V-Sit Hold|ABS||MAT|NONE|0|T|I|T|Balance on your hips with legs raised in a V and back straight.
Spiderman Plank|OBL|ABS|MAT|NONE|0|B|C|A|In a high plank, bring one knee to the same side elbow and return.
Dumbbell Clean and Press|FD|GL,Q,TRP|DB|DB|2|W|C|C|Clean the dumbbells to the shoulders and press them overhead.
Kneeling Hip Flexor Stretch|MOB|Q|MAT|NONE|0|T|I|M|Half kneeling, squeeze the back glute and shift the hips forward.
World's Greatest Stretch|MOB|GL,HM,UB|MAT|NONE|0|T|I|M|From a deep lunge, drop the elbow to the instep, then rotate the arm up.
Open Book Thoracic Rotation|MOB|UB,CH|MAT|NONE|0|T|I|M|Lying on your side, knees bent, open the top arm across and follow it with your eyes.
Running|CAR|Q,CAL,HM|BW|NONE|0|C|C|K|Run tall with relaxed shoulders and quick light steps.
Treadmill Walking (Incline)|CAR|GL,CAL,HM|TM|NONE|0|C|C|[20,40,1,0,1]|Walk briskly on a steep incline without holding the handrails.
Stationary Bike Intervals|CAR|Q,GL|BK|NONE|0|C|C|[15,25,1,0,1]|Alternate hard 30 second sprints with easy recovery spinning.
Jump Rope|CAR|CAL|BW|NONE|0|C|C|[10,20,1,0,1]|Stay on the balls of your feet and turn the rope with the wrists.
Jumping Jacks|CAR|CAL,SD|BW|NONE|0|T|C|T|Jump the feet out while raising the arms overhead, then back together.
High Knees|CAR|Q,ABS|BW|NONE|0|T|C|T|Run in place driving the knees to hip height with quick arm swings.
"""

COLS = ["Exercise", "Primary", "Secondary", "Equipment", "Load", "Implements", "Type",
        "Mechanics", "RepMin", "RepMax", "Sets", "RestSec", "SecPerRep", "Added", "Instructions"]


def parse(block, added):
    rows = []
    for ln, line in enumerate(block.strip("\n").split("\n"), 1):
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 10:
            sys.exit(f"bad field count ({len(parts)}) on line: {line}")
        name, p, sec, eq, load, impl, typ, mech, prof, instr = parts
        name = name.encode("utf-8").decode("unicode_escape") if "\\u" in name else name
        prim = M[p]
        secs = [M[s] for s in sec.split(",") if s]
        if prim in secs or len(secs) > 3 or len(set(secs)) != len(secs):
            sys.exit(f"bad secondary for {name}")
        eqs = [E[e] for e in eq.split(",") if e]
        if not eqs or (("Bodyweight" in eqs) and len(eqs) > 1):
            sys.exit(f"bad equipment for {name}")
        ld = "None" if load == "NONE" else E[load]
        if ld not in LOADS:
            sys.exit(f"bad load for {name}: {ld}")
        if ld != "None" and ld not in eqs:
            sys.exit(f"load not in equipment for {name}")
        impl = int(impl)
        if (ld == "None") != (impl == 0):
            sys.exit(f"implements/load mismatch for {name}")
        if prof.startswith("["):
            nums = tuple(int(x) for x in prof.strip("[]").split(","))
        else:
            nums = PROFILES[prof]
        if len(nums) != 5 or nums[0] > nums[1]:
            sys.exit(f"bad numbers for {name}")
        if '"' in instr or "'" in instr or len(instr.split()) > 22:
            sys.exit(f"bad instruction for {name}: {instr}")
        rows.append({
            "Exercise": name, "Primary": prim, "Secondary": "; ".join(secs),
            "Equipment": "; ".join(eqs), "Load": ld, "Implements": impl,
            "Type": TYPES[typ], "Mechanics": MECH[mech],
            "RepMin": nums[0], "RepMax": nums[1], "Sets": nums[2], "RestSec": nums[3],
            "SecPerRep": nums[4], "Added": "Yes" if added else "", "Instructions": instr,
        })
    return rows


def main():
    with open(SRC, encoding="utf-8", newline="") as f:
        src = list(csv.DictReader(f))
    hist = {r["Exercise"]: r for r in parse(HISTORY, False)}
    added = parse(ADDED, True)

    names = [r["Exercise"] for r in src]
    missing = [n for n in names if n not in hist]
    extra = [n for n in hist if n not in set(names)]
    if missing:
        print("NO SPEC (needs a line):", *missing, sep="\n  ")
    if extra:
        print("SPEC WITHOUT INPUT ROW:", *extra, sep="\n  ")
    if missing or extra:
        sys.exit(1)

    out = [hist[n] for n in names]  # keep input order, byte-exact names
    lower = {n.lower() for n in names}
    for r in added:
        if r["Exercise"].lower() in lower:
            sys.exit(f"added duplicates history: {r['Exercise']}")
        lower.add(r["Exercise"].lower())
        out.append(r)

    # multiplier sanity report
    for s in src:
        r = hist[s["Exercise"]]
        m = float(s["Multiplier"])
        if r["Implements"] == 2 and m < 2:
            print(f"note: impl 2 but multiplier {m}: {s['Exercise']}")
        if r["Implements"] == 1 and m == 4.0:
            print(f"note: impl 1 but multiplier 4: {s['Exercise']}")

    with open(DST, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(out)
    print(f"wrote {len(out)} rows ({len(names)} history + {len(added)} added) to {DST}")


if __name__ == "__main__":
    main()
