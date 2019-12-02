function getPosition(name) {
  switch (name) {
    /* SIDES */
    case 'top': return { x: 0, y: 0, width: 1, height: .5 };
    case 'right': return { x: .5, y: 0, width: .5, height: 1 };
    case 'bottom': return { x: 0, y: .5, width: 1, height: .5 };
    case 'left': return { x: 0, y: 0, width: .5, height: 1 };

    /* CORNERS */
    case 'top-left': return { x: 0, y: 0, width: .5, height: .5 };
    case 'top-right': return { x: .5, y: 0, width: .5, height: .5 };
    case 'bottom-right': return { x: .5, y: .5, width: .5, height: .5 };
    case 'bottom-left': return { x: 0, y: .5, width: .5, height: .5 };

    /* THIRDS */
    case 'left-1': return { x: 0, y: 0, width: 1/3, height: 1 };
    case 'left-2': return { x: 0, y: 0, width: 2/3, height: 1 };
    case 'right-1': return { x: 2/3, y: 0, width: 1/3, height: 1 };
    case 'right-2': return { x: 1/3, y: 0, width: 2/3, height: 1 };
  }
}

function getRelativePosition(name, window = Window.focused(), screen = Window.focused().screen()) {
  const windowFrame = window.frame();
  const screenFrame = screen.frame();

  const x = windowFrame.x - screenFrame.x;
  const y = windowFrame.y - screenFrame.y;
  const width = windowFrame.width;
  const height = windowFrame.height;

  const third = Math.floor(x / (screenFrame.width / 3));

  Phoenix.log({
    x: third / 3,
    y: window.y,
    width: screenFrame.width / 3,
    height: window.height,
  });
  Phoenix.log(third)
  Phoenix.log(screenFrame.width)


  Phoenix.log(x)
  Phoenix.log(y)
  Phoenix.log(width)
  Phoenix.log(height)
}
