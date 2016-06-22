"""Jordan Ogilvy, 19th June, 'pypong', a Pong clone implementation using pygame"""

import pygame
import math
import random
from myqueue import MyQueue

class Paddle:
	def __init__(self, display):
		self.__x = 0		# x and y co ordinates for the top left corner of the paddle, in absolute respect to the screen/surface
		self.__y = 0
		self.__height = 80	# width and height of paddle in pixels
		self.__width = 15
		self.__surface = pygame.Surface((self.__width, self.__height))	#the surface we draw the paddle to. It is then blitted to the display.
		self.__speed = 5	#speed of paddle in pixels per frame. speed is constant - paddle moves at this speed, or it doesnt move at all. also vertical.
		self.__display = display		#the display to draw the paddle surface on
		self.__colour = (255, 255, 255)	#RGB colour tuple. Not color.
		
	def get_rect(self):
		# return the x, y, width, and height of the paddle in a tuple. Used for collision checking
		return (self.__x, self.__y, self.__width, self.__height)
		
	def get_speed(self):
		return self.__speed
		
	def move_up(self):
		self.__y -= self.__speed
		
	def move_down(self):
		self.__y += self.__speed	
		
	def set_position(self, newx, newy):
		self.__x = newx
		self.__y = newy
		
	def update(self):
		#draw the paddle to surface, and blit the surface to the display. Thats it for the paddle
		self.__surface.fill(self.__colour)
		self.__display.blit(self.__surface, (self.__x, self.__y))
		
class Player(Paddle):
	# the point of the player havings its own class is to handle the player paddle and player keypress events separately
	# it keeps the main loop tidy
	def __init__(self, display):
		super(Player, self).__init__(display)
		self.__display = display
		self.set_position(605, 200)		#move the paddle to the right hand side of the screen at the start
		self.__press_move_up = False		#bools to control movement of the paddle
		self.__press_move_down = False
		self.__last_move = lambda *args: None		#track the direction the player paddle moved last. points to a method. 
	
	def update(self, events, objects):
		# handle the events. Check for the up and down arrows.
		for event in events:
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_UP:
					self.__press_move_up = True
				elif event.key == pygame.K_DOWN:
					self.__press_move_down = True
					
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_UP:
					self.__press_move_up = False
				elif event.key == pygame.K_DOWN:
					self.__press_move_down = False
					
		#	move the paddle
		if self.__press_move_up and self.__press_move_down:
			# if both keys are down, move in the direction of the key that was pressed first.
			self.__last_move()
		elif self.__press_move_up:
			self.move_up()
			self.__last_move = self.move_up
		elif self.__press_move_down:
			self.move_down()
			self.__last_move = self.move_down
		else:	# if no keys are being pressed, set last_move to a do nothing function using lambda
			self.__last_move = lambda *args: None
		
		# draw the paddle (through its update method)
		super(Player, self).update()
		
class Opponent(Paddle):
	def __init__(self, display):
		super(Opponent, self).__init__(display)
		self.__display = display
		self.__brain = MyQueue()	# a list that tracks the balls position on different frames. Used for simulating delayed reaction time
		self.__reaction_time = 5	# reaction time of AI in frames
		self.__difficulties = (self.__ai_easy, self.__ai_normal, self.__ai_hard)
		self.__current_difficulty = 0		#0 for easy, 1 for normal, 2 for hard
		self.__winfo = pygame.display.Info()
		self.set_position(15, 200)	#move the ai paddle to the left side of the screen

	def set_difficulty(self, new_difficulty):
		# new_difficulty must be an int between 0-2. 0 for easy, 1 for normal, 2 for hard
		self.__current_difficulty = new_difficulty
		
	# the ai methods of the opponent. different thinking process for each difficulty	
	def __ai_base(self, ball, reaction_time):
		self.__reaction_time = reaction_time
		while(self.__brain.size()>self.__reaction_time):
			self.__brain.dequeue()
	
		self.__brain.enqueue(ball.get_position())	#add the position of the ball to the brain delay queue
		# only check the ball position and move to it if the ball is on screen
		if ball.is_in_play():
			if self.__brain.size()>self.__reaction_time:
				ball_position = self.__brain.dequeue()	#get the position of the ball from reaction_time frames ago, in a (x, y) tuple
				paddle_rect = self.get_rect()
				paddle_speed = self.get_speed()
				# move the ai paddle towards the balls y position, making sure they dont move off the screen
				if paddle_rect[1]+paddle_rect[3]//2 < ball_position[1] - paddle_speed and \
				paddle_rect[1]+paddle_rect[3]<self.__winfo.current_h:
					self.move_down()
				elif paddle_rect[1]+paddle_rect[3]//2 > ball_position[1] + paddle_speed and \
				paddle_rect[1]>0:
					self.move_up()
	
	def __ai_easy(self, ball):
		#same as ai_normal but with a slower reaction time
		self.__ai_base(ball, 14)
		
	def __ai_normal(self, ball):
		self.__ai_base(ball, 8)
	
	def __ai_hard(self, ball):
		#same as ai_normal but with a faster reaction time, and moves to the middle after returning a shot.
		self.__reaction_time = 3
		while(self.__brain.size()>self.__reaction_time):
			self.__brain.dequeue()
	
		self.__brain.enqueue(ball.get_position())
		if ball.is_in_play():
			if self.__brain.size()>self.__reaction_time:
				paddle_rect = self.get_rect()
				paddle_speed = self.get_speed()
				ball_position = self.__brain.dequeue()	#get the position of the ball from reaction_time frames ago, in a (x, y) tuple
				ball_direction = ball.get_direction()
				# if the ball is moving away from the ai, move towards the middle of the screen
				if math.cos(ball_direction)>0:		#assumes ai is on the left
					if paddle_rect[1]+paddle_rect[3]//2<self.__winfo.current_h//2-paddle_speed:
						self.move_down()
					elif paddle_rect[1]+paddle_rect[3]//2>self.__winfo.current_h//2+paddle_speed:
						self.move_up()
				# otherwise move the ai paddle towards the balls y position, making sure they dont move off the screen
				else:
					if paddle_rect[1]+paddle_rect[3]//2 < ball_position[1] - paddle_speed and \
					paddle_rect[1]+paddle_rect[3]<self.__winfo.current_h:
						self.move_down()
					elif paddle_rect[1]+paddle_rect[3]//2 > ball_position[1] + paddle_speed and \
					paddle_rect[1]>0:
						self.move_up()
			
		
	def update(self, events, objects):	
		for object in objects:
			if isinstance(object, Ball):
				#call the ai method for the opponent. Moves the paddle based on the ball and its own positions'
				self.__difficulties[self.__current_difficulty](object)	
		
		#update the paddle
		super(Opponent, self).update()		

class Ball:
	def __init__(self, display):
		self.__display = display
		self.__size = 16		#the ball is a square
		self.__surface = pygame.Surface((self.__size, self.__size))
		self.__colour = (255, 255, 255)
		self.__velocity = 0	# current velocity of the ball in pixels per frame
		self.__direction = 0	#direction of the ball in radians, 0 is right, pi/2 is up.
		self.__hspeed = 0
		self.__vspeed = 0 	#2d speed components of the 
		self.__x = 0
		self.__y = 0	#coords of the top left corner of the ball
		#between 0 and pi/2, the  max angle from the horizontal in either direction the ball bounces from a paddle
		self.__max_bounce_angle = math.pi/5
		self.__next_x = self.__x + self.__hspeed
		self.__next_y = self.__y + self.__vspeed
		
	def get_size(self):
		return self.__size
		
	def get_position(self):
		return (self.__x, self.__y)
		
	def get_direction(self):
		return self.__direction
	
	def set_position(self, newx, newy):
		self.__x = newx
		self.__y = newy
		
	def set_velocity(self, new_velocity):
		self.__velocity = new_velocity
		self.__calculate_speed_components()
		
	def set_direction(self, new_direction):
		self.__direction = new_direction
		self.__calculate_speed_components()
		
	def __calculate_speed_components(self):
		self.__hspeed = self.__velocity*math.cos(self.__direction)
		self.__vspeed = self.__velocity*math.sin(self.__direction)
		
	def set_direction_random(self, base_direction, error):
		# set direction to a random direction plus or minus a random value within the range of the specified error. All in radians
		offset = random.uniform(0, error*2)
		self.__direction = base_direction + error - offset
		self.__calculate_speed_components()
		
	def is_in_play(self):
		w = pygame.display.Info().current_w
		return (self.__x > 0 and self.__x < w)
		
	def __check_wall_collision(self):
		#check for collisions with the top and bottom of the screen
		winfo = pygame.display.Info()
		if self.__next_y < 0 or self.__next_y > winfo.current_h-self.__size:
			self.__vspeed = -self.__vspeed	#bounce of the walls by reversing the vertical direction (walls are only top and bottom)
			try:	#beware of division by 0 when working out the new direction based on the 2d speeds
				self.__direction = math.atan(self.__vspeed/self.__hspeed)
				if self.__hspeed<0:
					self.__direction += math.pi
			except ZeroDivisionError:
				self.__direction = 0
	
	def __check_paddle_collision(self, objects):
		for paddle in objects:
			if isinstance(paddle, Paddle):
				#for every paddle in the objects list, check if the ball will overlap with the paddle in the next frame
				x1, y1, w1, h1 = self.__next_x, self.__next_y, self.__size, self.__size
				(x2, y2, w2, h2) = paddle.get_rect()
				if not (x2>x1+w1 or x2+w2<x1 or y1+h1<y2 or y1>y2+h2):	#AABB collision check
					#after colliding with a paddle, the ball bounces back the other way (left->right) in a direction within a random cone
					if self.__hspeed<0:	#if going left, go right in a random direction
						new_base_direction = 0
					else:	#otherwise we must be going right, so change to going left
						new_base_direction = math.pi
					#set the new direction
					self.set_direction_random(new_base_direction, self.__max_bounce_angle)
					# post an event so the main game loop will see it and change the background colour
					hit_event = pygame.event.Event(pygame.USEREVENT+4)
					pygame.event.post(hit_event)
		
	def update(self, events, objects):			
		#calculate the would-be position of the ball in the next frame, based on the current direction and velocity.
		self.__calculate_speed_components()
		self.__next_x = self.__x + self.__hspeed
		self.__next_y = self.__y - self.__vspeed
		
		#handle collisions
		self.__check_wall_collision()
		self.__check_paddle_collision(objects)	
			
		#move the balll
		self.__x += self.__hspeed
		self.__y -= self.__vspeed	#subtract because the pygame window has 0 at the top, not the bottom
		
		#draw the ball
		self.__surface.fill(self.__colour)
		self.__display.blit(self.__surface, (self.__x, self.__y))
		
# restarts points when player/opponent wins round, keeps score and prints it		
class MatchController:
	def __init__(self, display):
		self.__display = display
		self.__player_score = 0
		self.__opponent_score = 0
		self.__restart_wait_time = 2000	# time in milliseconds between the ball returning to the center, and the ball starting moving
		winfo = pygame.display.Info()
		self.__centre_x = winfo.current_w//2
		self.__centre_y = winfo.current_h//2
		self.__centre_line_width = 2
		self.__centre_line_surface = pygame.Surface((self.__centre_line_width, winfo.current_h))	#surface to draw the centre line on
		self.__draw_colour = (255, 255, 255)		#draw colour for text and centre line, RGB tuple
		self.__ball_speed = 12		# speed the ball moves at in pixels per frame
		self.__score_font = pygame.font.SysFont("Arial", 48)
		self.__score_limit = 7
		self.__max_serve_angle = math.pi/8		# max angle from horizontal in radians the ball can move on a serve
		
	def set_ball_speed(self, new_speed):
		self.__ball_speed = new_speed
		
	def set_max_serve_angle(self, new_angle):
		self.__max_serve_angle = new_angle		#remember, its all in radians
		
	def __centre_ball(self, ball):
		# called when somebody wins a point. Increments the scores, sets a timer, and moves the ball to the centre.
		ball_position = ball.get_position()
		if ball_position[0]<0:		#increment the score of whoever won the point. determined by balls position off screen
			self.__player_score += 1
		elif ball_position[0]>self.__centre_x*2:
			self.__opponent_score += 1
		# set a timer that when reaches 0 triggers the event "userevent+1". in milliseconds (approximate)
		pygame.time.set_timer(pygame.USEREVENT+1, self.__restart_wait_time)
		# stop the ball moving and place it in the centre of the screen
		ball.set_velocity(0)
		ball.set_position(self.__centre_x-ball.get_size()//2, self.__centre_y-ball.get_size()//2)
	
	def __restart_ball(self, ball):
		#disable the timer calling userevent+15
		pygame.time.set_timer(pygame.USEREVENT+1, 0)
		base_direction = random.choice((0,  math.pi))	# left or right
		ball.set_direction_random(base_direction, self.__max_serve_angle)
		ball.set_velocity(self.__ball_speed)
	
	def __check_for_winner(self, objects):
		def setstr(newstr, win_event, objects):
			pygame.event.post(win_event)
			for controller in objects:
				if isinstance(controller, GameController):
					controller.set_result_string(newstr)
						
		# called at the end of each point. Check if the player or opponent won. If so, post an event to notify other objects
		win_event = pygame.event.Event(pygame.USEREVENT+2)
		if self.__player_score == self.__score_limit:
			setstr("You Won!", win_event, objects)
		if self.__opponent_score == self.__score_limit:
			setstr(" You Lost :(", win_event, objects)
			
	def update(self, events, objects):
		need_restart = False
		for event in events:
			if event.type == pygame.USEREVENT+1:
				#if this event fires, it means we need to tell the ball to start moving again
				need_restart = True
				# if the ball is not in play, somebody must have won the point, so restart it
				
		for ball in objects:
			if isinstance(ball, Ball):
				if not ball.is_in_play():
					self.__centre_ball(ball)
					self.__check_for_winner(objects)
				if need_restart:
					self.__restart_ball(ball)
					
		# draw the centre line
		self.__centre_line_surface.fill(self.__draw_colour)
		self.__display.blit(self.__centre_line_surface, (self.__centre_x-self.__centre_line_width//2, 0))
		# draw the scores
		player_label = self.__score_font.render(str(self.__player_score), 1, self.__draw_colour)
		opponent_label = self.__score_font.render(str(self.__opponent_score), 1, self.__draw_colour)
		self.__display.blit(player_label, (self.__centre_x+50-player_label.get_width()//2, 20))
		self.__display.blit(opponent_label, (self.__centre_x-50-opponent_label.get_width()//2, 20))

class GameController:
	def __init__(self, display):
		self.__display = display
		self.__font_name = "Arial"
		self.__big_font = pygame.font.SysFont(self.__font_name, 48)
		self.__small_font = pygame.font.SysFont(self.__font_name, 18)
		self.__state = "start"		# "start", "difficulty", "game", or "endgame".
		self.__draw_colour = (255, 255, 255)	#RGB colour tuple
		self.__result_string = None	#placeholder for "You won!" or "You lost!"
		self.__play_label = self.__big_font.render("Press 'P' To Play Again", 1, self.__draw_colour)
		self.__quit_label = self.__small_font.render("Or press 'Q' to quit", 1, self.__draw_colour)
		self.__difficulties = (self.start_easy_game, self.start_normal_game, self.start_hard_game)
		self.__current_difficulty = 1
		
	def set_result_string(self, newstring):
		self.__result_string = newstring

	def start_easy_game(self, objects):
		self.__current_difficulty = 0
		o = Opponent(self.__display)
		m = MatchController(self.__display)
		o.set_difficulty(self.__current_difficulty)
		m.set_ball_speed(10)
		m.set_max_serve_angle(math.pi/36)
		objects+=[o, m, Player(self.__display), Ball(self.__display)]
		self.__state = "game"
		
	def start_normal_game(self, objects):
		self.__current_difficulty = 1
		o = Opponent(self.__display)
		m = MatchController(self.__display)
		o.set_difficulty(self.__current_difficulty)
		m.set_ball_speed(12)
		m.set_max_serve_angle(math.pi/18)
		objects+=[o, m, Player(self.__display), Ball(self.__display)]
		self.__state = "game"
		
	def start_hard_game(self, objects):
		self.__current_difficulty = 2
		o = Opponent(self.__display)
		m = MatchController(self.__display)
		o.set_difficulty(self.__current_difficulty)
		m.set_ball_speed(14)
		m.set_max_serve_angle(math.pi/12)
		objects+=[o, m, Player(self.__display), Ball(self.__display)]
		self.__state = "game"
		
	def update(self, events, objects):		
		for event in events:
			# if the match is over (player or opponent wins)
			if event.type == pygame.USEREVENT+2:
				# remove all objects that aren't the gamecontroller, and change the game state
				objects.clear()
				objects+=[self]
				self.__state = "endgame"
				
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					#if the player quits
					if self.__state=="start" or self.__state=="endgame":
						quit_event = pygame.event.Event(pygame.QUIT)
						pygame.event.post(quit_event)
						
				elif event.key == pygame.K_p:
					#if the player wants to start a game
					if self.__state=="start":
						# go to the difficulty selection screen
						self.__state = "difficulty"
					#if the player wants a rematch, start with the currently selected difficulty
					elif self.__state=="endgame":
						self.__difficulties[self.__current_difficulty](objects)
						
				elif event.key == pygame.K_e and self.__state == "difficulty":
					self.start_easy_game(objects)
				elif event.key == pygame.K_n and self.__state == "difficulty":
					self.start_normal_game(objects)
				elif event.key == pygame.K_h and self.__state == "difficulty":
					self.start_hard_game(objects)
					
				elif event.key == pygame.K_d and self.__state == "endgame":
					self.__state = "difficulty"
				
		# alter the text the gamecontroller displays based on the current game state
		winfo = pygame.display.Info()
		w = winfo.current_w
		h = winfo.current_h
		
		if self.__state == "start":
			self.__play_label = self.__big_font.render("Press 'P' To Play", 1, self.__draw_colour)
			self.__display.blit(self.__play_label, (w//2-self.__play_label.get_width()//2, h//2-self.__play_label.get_height()))
			self.__display.blit(self.__quit_label, (w//2-self.__quit_label.get_width()//2, h//2+self.__quit_label.get_height()))	
			
		elif self.__state == "endgame":
			self.__play_label = self.__big_font.render("Press 'P' To Play Again", 1, self.__draw_colour)
			result_label = self.__big_font.render(self.__result_string, 1, self.__draw_colour)
			difficulty_label = self.__small_font.render("Press 'D' To Change Difficulty", 1, self.__draw_colour)
			self.__display.blit(result_label, (w//2-result_label.get_width()//2, 100))
			self.__display.blit(self.__play_label, (w//2-self.__play_label.get_width()//2, h//2-self.__play_label.get_height()))
			self.__display.blit(difficulty_label, (w//2-difficulty_label.get_width()//2, h//2+difficulty_label.get_height()))
			self.__display.blit(self.__quit_label, (w//2-self.__quit_label.get_width()//2, h//2+self.__quit_label.get_height()*2))
			
		elif self.__state == "difficulty":
			difficulty_label = self.__big_font.render("Select a difficulty", 1, self.__draw_colour)
			easy_label = self.__big_font.render("[E]asy", 1, self.__draw_colour)
			normal_label = self.__big_font.render("[N]ormal", 1, self.__draw_colour)
			hard_label = self.__big_font.render("[H]ard", 1, self.__draw_colour)
			self.__display.blit(difficulty_label, (w//2-difficulty_label.get_width()//2, 80))
			x = w//2 - max(easy_label.get_width(), normal_label.get_width(), hard_label.get_width())//2
			self.__display.blit(easy_label, (x, 160))
			self.__display.blit(normal_label, (x, 170+easy_label.get_height()))
			self.__display.blit(hard_label, (x, 180+2*easy_label.get_height()))
			
		
class MyGame:
	def __init__(self):
		self.window_width = 640
		self.window_height = 480
		# start in windowed mode, not fullscreen
		self.game_window = pygame.display.set_mode((self.window_width, self.window_height),  pygame.HWSURFACE | pygame.DOUBLEBUF)
		pygame.display.set_caption("Pink Pong")
		self.clock = pygame.time.Clock()
		self.objects = [GameController(self.game_window)]
		self.back_colourq = (255,20,147) #RGB colour tuple for some shade of pink, arguably purple
		self.game_speed = 60	#frames per second
		#start the game loop
		self.game_loop()

	def game_loop(self):
		while True:
			self.clock.tick(self.game_speed)		#have a lower framerate to give greater control over speed of game objects
			# Process events
			events = pygame.event.get()
			for event in events:
				if event.type == pygame.QUIT:
					return
				#this event is posted on every collision between the ball and a paddle, or when a point is won. Change the background colour each time
				#elif event.type == pygame.USEREVENT+4:
					#r,g,b = random.randrange(256), random.randrange(256), random.randrange(256)
					#while ((r>170 and g>170) or  (r>170 and b>170) or (b>170 and g>170)):	#make sure the new background colour isnt white/light grey
						#r,g,b = random.randrange(256), random.randrange(256), random.randrange(256)
					#self.back_colour = (r,g,b)
					
			# Clear the screen to black
			self.game_window.fill(self.back_colour)
			# put stuff on the screen by updating all the objects
			for object in self.objects:
				object.update(events, self.objects)
			# update the screen
			pygame.display.update()
			
if __name__=="__main__":
	pygame.init()
	game = MyGame()
	
