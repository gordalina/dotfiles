function setFrame({x, y, width, height, window = Window.focused(), screen = Window.focused().screen()}) {
  const frame = screen.flippedVisibleFrame();

  window.setFrame ({
    x: frame.x + (frame.width * x),
    y: frame.y + (frame.height * y),
    width: frame.width * width,
    height: frame.height * height
  });
}

function moveToScreen({window = Window.focused(), offset = 0}) {
  const windowFrame = window.frame();
  const screenFrame = window.screen().flippedVisibleFrame();

  setFrame({
    x: Math.abs((windowFrame.x - screenFrame.x) / screenFrame.width),
    y: Math.abs((windowFrame.y - screenFrame.y) / screenFrame.height),
    width: Math.abs(windowFrame.width / screenFrame.width),
    height: Math.abs(windowFrame.height / screenFrame.height),
    window,
    screen: getScreenFromOffset({window, offset}),
  });
}
