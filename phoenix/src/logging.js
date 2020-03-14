// to start the log type:
// log stream --process Phoenix
function log() {
  const window = Window.focused().frame();
  const screen = Window.focused().screen().frame()
  const frame = Window.focused().screen().flippedVisibleFrame();

  Phoenix.log(JSON.stringify({
    window: {
      x: window.x,
      y: window.y,
      width: window.width,
      height: window.height,
    },
    screen: {
      x: screen.x,
      y: screen.y,
      width: screen.width,
      height: screen.height,
    },
    frame: {
      x: frame.x,
      y: frame.y,
      width: frame.width,
      height: frame.height,
    },
  }, null, 2));
}
