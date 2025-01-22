import pygame
import sys
from pygame.locals import QUIT

class Menu:
    def __init__(self, displaysurf):
        self.displaysurf = displaysurf
        self.btn_count = 0
        self.btn_max = 0
        self.all_buttons = pygame.sprite.Group()

    def scroll(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                if self.btn_count == 0:
                    self.btn_count = self.btn_max
                else:
                    self.btn_count -= 1

            if event.key in [pygame.K_DOWN, pygame.K_s]:
                if self.btn_count == self.btn_max:
                    self.btn_count = 0
                else:
                    self.btn_count += 1

    def pressReturn(self, event):
        pass

    def drawButtons(self):
        for entity in self.all_buttons:
            entity.update(self.btn_count)
            self.displaysurf.blit(entity.surf, entity.origin)


class StartMenu(Menu):
    def __init__(self, displaysurf):
        super().__init__(displaysurf)
        self.btn_max = 1
        self.btn1 = Button('Start Game', (329, 448), 0)
        self.btn2 = Button('Exit', (329, 576), 1)
        self.all_buttons.add(self.btn1)
        self.all_buttons.add(self.btn2)
        self.font = pygame.font.Font("font/minecraft.ttf", 64)

    def pressReturn(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.btn_count == 0:  # "Start Game"
                    return "start_game"
                elif self.btn_count == 1:  # "Exit"
                    return "exit"

    def drawLogo(self):
        self.displaysurf.fill((0, 0, 0))  # Черный фон
        logo_font = pygame.font.Font("font/minecraft.ttf", 128)
        title = logo_font.render('DUNGEON SANDBOX', True, (255, 255, 255))
        self.displaysurf.blit(title, (180, 200))


class Button(pygame.sprite.Sprite):
    def __init__(self, text, origin, number):
        super().__init__()
        self.text = text
        self.origin = origin
        self.number = number
        self.font = pygame.font.Font("font/minecraft.ttf", 64)
        self.SHADOW = (64, 64, 64)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.surf = pygame.Surface((400, 100))
        self.surf.fill(self.SHADOW)
        self.surf.blit(self.font.render(self.text, True, self.BLACK), (20, 20))

    def update(self, btn_count):
        if btn_count == self.number:
            self.surf.fill(self.WHITE)
        else:
            self.surf.fill(self.SHADOW)
        self.surf.blit(self.font.render(self.text, True, self.BLACK), (20, 20))


def main():
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
    displaysurf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Dungeon Sandbox')
    clock = pygame.time.Clock()

    # Создаем объект стартового меню
    start_menu = StartMenu(displaysurf)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            start_menu.scroll(event)
            result = start_menu.pressReturn(event)
            if result == "start_game":
                print("Game Started!")  # Здесь интеграция с игровой логикой
                running = False
            elif result == "exit":
                pygame.quit()
                sys.exit()

        start_menu.drawLogo()
        start_menu.drawButtons()
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()