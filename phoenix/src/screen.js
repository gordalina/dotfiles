function getScreenFromOffset({window = Window.focused(), offset = 0}) {
  const currentScreen = window.screen();
  const screens = Screen.all();

  const currentIndex = screens.indexOf(currentScreen);

  let newIndex = currentIndex + offset;
  if (newIndex < 0) {
    newIndex += screens.length;
  } else if (newIndex >= screens.length) {
    newIndex -= screens.length;
  }

  return screens[newIndex];
}
