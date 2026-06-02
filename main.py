from math import sqrt
from enum import Enum

import pyray
from pyray import (
    DARKGRAY,
    RED,
    BLACK,
    GRAY,
    LIGHTGRAY,
)


# Initialization
global g_evening_out, g_even_out_target
g_evening_out = False

G = 850
PLAYER_JUMP_SPD = 500.0
PLAYER_HOR_SPD = 250.0

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450

pyray.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, 'raylib [core] example - 2d camera')



# Raylib Math
def vector2_subtract(v1, v2):
    return pyray.Vector2(v1.x - v2.x, v1.y - v2.y)


def vector2_add(v1, v2):
    return pyray.Vector2(v1.x + v2.x, v1.y + v2.y)


def vector2_length(v):
    return sqrt((v.x * v.x) + (v.y * v.y))


def vector2_scale(v, scale):
    return pyray.Vector2(v.x * scale, v.y * scale)

class EnemyState(Enum):

	ALIVE = 1
	DEAD = 2
	PAUSED = 3

class Msg:

	def __init__(self,text,position,fontsize):

		self.text = text
		self.position = position
		self.fontsize = fontsize
		self.active = True
		self.timer = 135
		self.offset = pyray.Vector2(20,-50)


	def update(self, player):

		self.position.x = player.position.x+self.offset.x
		self.position.y = player.position.y+self.offset.y

		if self.timer > 0:

			self.timer -= 1

		else:
			self.active = False

	def draw(self):

		pyray.draw_text(self.text,int(self.position.x),
									int(self.position.y),
									int(self.fontsize),
									BLACK)

class MsgManager:

	def __init__(self, initlist,player):

		self.list = initlist

	def addmsg(self,newlist):

		for msg in newlist:
			self.list.append(msg)

	def update(self):

		for msg in self.list:
			if msg.active:
				msg.update(player)

	def draw(self):

		for msg in self.list:
			msg.draw()

class Player:

    def __init__(self, position, speed, can_jump):
        self.position = position
        self.speed = speed
        self.can_jump = can_jump
        self.dead = False
        self.rect = pyray.Rectangle(self.position.x,
									self.position.y,
									40,40)

    def update(self):

		#FOR COLLISION CALCULATION
        self.rect = pyray.Rectangle(self.position.x-20,
									self.position.y-40,
									40,40)
		
    def _initposition(self):

        self.position = pyray.Vector2(450, 180)

class Piranha:

	def __init__(self,position,speed,initstate,offset,msgman):
		self.position = position
		self.speed = speed
		self.initspeed = self.speed
		self.state = initstate
		self.timeoffset = offset
		self.msgman = msgman


		self.counter = 100 - self.timeoffset
		self.initcounter = self.counter
		self.direction = True
		self.size = 15

	def _state(self):

		match self.state:

			case EnemyState.ALIVE:
				self.jump()
			case EnemyState.DEAD:
				pass
			case EnemyState.PAUSED:
				pass

	def jump(self):

		
		if self.counter <= 0:
			self.direction = not self.direction
			self.counter = self.initcounter
			self.speed = self.initspeed

		if self.direction:
			self.position.y -= self.speed
			self.speed += 0.3
			self.counter -= 1

		else:
			self.position.y += self.speed
			self.speed += 0.3
			self.counter -= 1
		 
	def check_collision(self,player):
		selfvector = pyray.Vector2(self.position.x,self.position.y)
		if pyray.check_collision_circle_rec(selfvector,self.size,player.rect):

			newmsg = Msg("You DIED!",player.position,50)
			self.msgman.addmsg([newmsg])
			player._initposition()

	def draw(self):
		#print("hola me estoy dibujando: ", self.position.x, self.position.y)
		pyray.draw_circle_v(pyray.Vector2(self.position.x,self.position.y),
							self.size,pyray.DARKPURPLE)

	def update(self,player):
		
		self.check_collision(player)
		self._state()
		



class EnemyGroup:

	def __init__(self,initlist):
		
		self.initlist = initlist

	def update(self,player):

		for  enemy in self.initlist:
			enemy.update(player)

	def draw(self):

		for enemy in self.initlist:
			enemy.draw()

class EnvItem:

    def __init__(self, rect, blocking, color):
        self.rect = rect
        self.blocking = blocking
        self.color = color


def update_player(player, env_items, delta):
    if pyray.is_key_down(pyray.KeyboardKey.KEY_LEFT):
        player.position.x -= PLAYER_HOR_SPD * delta
    if pyray.is_key_down(pyray.KeyboardKey.KEY_RIGHT):
        player.position.x += PLAYER_HOR_SPD * delta
    if pyray.is_key_down(pyray.KeyboardKey.KEY_SPACE) and player.can_jump:
        player.speed = -PLAYER_JUMP_SPD
        player.can_jump = False

    hit_obstacle = False
    for ei in env_items:
        p = player.position
        if (
                ei.blocking and
                ei.rect.x <= p.x and
                ei.rect.x + ei.rect.width >= p.x and
                ei.rect.y >= p.y and
                ei.rect.y < p.y + player.speed * delta
        ):
            hit_obstacle = True
            player.speed = 0.0
            p.y = ei.rect.y

    if not hit_obstacle:
        player.position.y += player.speed * delta
        player.speed += G * delta
        player.can_jump = False
    else:
        player.can_jump = True


def update_camera_center(
        camera, player, env_items, delta, width, height
):
    camera.offset = pyray.Vector2(width / 2, height / 2)
    camera.target = player.position


def update_camera_center_inside_map(
        camera, player, env_items, delta, width, height
):
    camera.target = player.position
    camera.offset = pyray.Vector2(width / 2, height / 2)

    minX = 1000
    minY = 1000
    maxX = -1000
    maxY = -1000

    for ei in env_items:
        minX = min(ei.rect.x, minX)
        maxX = max(ei.rect.x + ei.rect.width, maxX)

        minY = min(ei.rect.y, minY)
        maxY = max(ei.rect.y + ei.rect.height, maxY)

    wmax = pyray.get_world_to_screen_2d(pyray.Vector2(maxX, maxY), camera)
    wmin = pyray.get_world_to_screen_2d(pyray.Vector2(minX, minY), camera)

    if wmax.x < width:
        camera.offset.x = width - (wmax.x - width / 2)
    if wmax.y < height:
        camera.offset.y = height - (wmax.y - height / 2)
    if wmin.x > 0:
        camera.offset.x = width / 2 - wmin.x
    if wmin.y > 0:
        camera.offset.y = height / 2 - wmin.y


def update_camera_center_smooth_follow(
        camera, player, env_items, delta, width, height
):
    min_speed = 40
    min_effect_length = 10
    fraction_speed = 6.5

    camera.offset = pyray.Vector2(width / 2, height / 2)
    diff = vector2_subtract(player.position, camera.target)
    length = vector2_length(diff)

    if length > min_effect_length:
        speed = max(fraction_speed * length, min_speed)
        camera.target = vector2_add(
            camera.target, vector2_scale(diff, speed * delta / length)
        )


def update_camera_even_out_on_landing(
        camera, player, env_items, delta, width, height
):
    global g_evening_out, g_even_out_target

    even_out_speed = 700

    camera.offset = pyray.Vector2(width / 2, height / 2)
    camera.target.x = player.position.x

    if g_evening_out:
        if g_even_out_target > camera.target.y:
            camera.target.y += even_out_speed * delta

            if camera.target.y > g_even_out_target:
                camera.target.y = g_even_out_target
                g_evening_out = False
        else:
            camera.target.y -= even_out_speed * delta
            if camera.target.y < g_even_out_target:
                camera.target.y = g_even_out_target
                g_evening_out = False
    else:
        if (
                player.can_jump and
                (player.speed == 0) and
                (player.position.y != camera.target.y)
        ):
            g_evening_out = True
            g_even_out_target = player.position.y


def update_camera_player_bounds_push(
        camera, player, env_items, delta, width, height
):
    bbox = pyray.Vector2(0.2, 0.2)

    bbox_world_min = pyray.get_world_to_screen_2d(
        pyray.Vector2((1 - bbox.x) * 0.5 * width,
                      (1 - bbox.y) * 0.5 * height),
        camera
    )
    bbox_world_max = pyray.get_world_to_screen_2d(
        pyray.Vector2((1 + bbox.x) * 0.5 * width,
                      (1 + bbox.y) * 0.5 * height),
        camera
    )
    camera.offset = pyray.Vector2((1 - bbox.x) * 0.5 * width,
                                  (1 - bbox.y) * 0.5 * height)

    if player.position.x < bbox_world_min.x:
        camera.target.x = player.position.x
    if player.position.y < bbox_world_min.y:
        camera.target.y = player.position.y
    if player.position.x > bbox_world_max.x:
        camera.target.x = (
                bbox_world_min.x + (player.position.x - bbox_world_max.x)
        )
    if player.position.y > bbox_world_max.y:
        camera.target.y = (
                bbox_world_min.y + (player.position.y - bbox_world_max.y)
        )


# Main intialization
player = Player(pyray.Vector2(450, 180), 0, False)

msginit = Msg("Go to the right!",player,40)
msgman = MsgManager([msginit],player)

env_items = (
    EnvItem(pyray.Rectangle(0, 0, 1000, 400), 0, LIGHTGRAY),
    EnvItem(pyray.Rectangle(0, 400, 1000, 200), 1, GRAY),
    EnvItem(pyray.Rectangle(300, 200, 400, 10), 1, GRAY),
    EnvItem(pyray.Rectangle(250, 300, 100, 10), 1, GRAY),
    EnvItem(pyray.Rectangle(650, 300, 100, 10), 1, GRAY),
	EnvItem(pyray.Rectangle(850, 200, 50, 2000),1,BLACK),
	EnvItem(pyray.Rectangle(1050, 100, 50, 2000),1,BLACK),
	EnvItem(pyray.Rectangle(1250, 0, 50, 2000),1,BLACK),
	EnvItem(pyray.Rectangle(1450, 0, 50, 2000),1,BLACK),
	EnvItem(pyray.Rectangle(1650, 0, 50, 2000),1,BLACK),
	EnvItem(pyray.Rectangle(1850, 0, 50, 2000),1,BLACK)
)

piranha1 = Piranha(pyray.Vector2(1525,300),3,EnemyState.ALIVE,0,msgman)
piranha2 = Piranha(pyray.Vector2(1725,300),3,EnemyState.ALIVE,30,msgman)
piranha3 = Piranha(pyray.Vector2(1785,300),4,EnemyState.ALIVE,0,msgman)

enemygroupMain = EnemyGroup([piranha1,piranha2,piranha3])

camera = pyray.Camera2D()
camera.target = player.position
camera.offset = pyray.Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
camera.rotation = 0.0
camera.zoom = 1.0

pyray.set_target_fps(60)  # Set our game to run at 60 frames-per-second

# Store pointers to the multiple update camera functions
camera_updaters = (
    update_camera_center,
    update_camera_center_inside_map,
    update_camera_center_smooth_follow,
    update_camera_even_out_on_landing,
    update_camera_player_bounds_push,
)
camera_option = 2
camera_updaters_length = len(camera_updaters)

camera_descriptions = (
    'Follow player center',
    'Follow player center, but clamp to map edges',
    'Follow player center smoothed',
    ('Follow player center horizontally '
     'update player center vertically after landing'),
    'Player push camera on getting too close to screen edge',
)

# Main game loop
while not pyray.window_should_close():  # Detect window close button or ESC key
    # Update
    delta_time = pyray.get_frame_time()

    update_player(player, env_items, delta_time)
    msgman.update()
    player.update()
    enemygroupMain.update(player)

    camera.zoom += pyray.get_mouse_wheel_move() * 0.05

    if camera.zoom > 3.0:
        camera.zoom = 3.0
    elif camera.zoom < 0.25:
        camera.zoom = 0.25

    if pyray.is_key_pressed(pyray.KeyboardKey.KEY_R):
        camera.zoom = 1.0
        player.position = pyray.Vector2(450, 180)

    if pyray.is_key_pressed(pyray.KeyboardKey.KEY_C):
        camera_option = (camera_option + 1) % camera_updaters_length

    # Call update camera function by its pointer
    camera_updaters[camera_option](
        camera, player, env_items, delta_time,
        SCREEN_WIDTH, SCREEN_HEIGHT
    )

    # Draw
    pyray.begin_drawing()
    pyray.clear_background(LIGHTGRAY)

    pyray.begin_mode_2d(camera)

    for env_item in env_items:
        pyray.draw_rectangle_rec(env_item.rect, env_item.color)

    player_rect = pyray.Rectangle(
        int(player.position.x) - 20,
        int(player.position.y) - 40,
        40, 40
    )
    enemygroupMain.draw()
    msgman.draw()

    pyray.draw_rectangle_rec(player_rect, RED)
    pyray.draw_rectangle_rec(player.rect,pyray.Color(255,255,150,50))

    pyray.end_mode_2d()

    pyray.draw_text('Controls:', 20, 20, 10, BLACK)
    pyray.draw_text('- Right/Left to move', 40, 40, 10, DARKGRAY)
    pyray.draw_text('- Space to jump', 40, 60, 10, DARKGRAY)
    pyray.draw_text('- Mouse Wheel to Zoom in-out, R to reset zoom',
                    40, 80, 10, DARKGRAY)
    pyray.draw_text('- C to change camera mode', 40, 100, 10, DARKGRAY)
    pyray.draw_text('Current camera mode:', 20, 120, 10, BLACK)
    pyray.draw_text(camera_descriptions[camera_option], 40, 140, 10, DARKGRAY)
    pyray.draw_text("PRUEBA DE NUITKA 1.1",50,250,20,RED)

    pyray.end_drawing()

# De-Initialization
pyray.close_window()  # Close window and OpenGL context