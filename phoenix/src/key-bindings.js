const handles = {
  // window position in screen
  left: new Key('left', ['ctrl', 'alt'], () =>
    setFrame(getPosition('left'))),
  right: new Key('right', ['ctrl', 'alt'], () =>
    setFrame(getPosition('right'))),

  // halve the window height
  top_half: new Key('up', ['ctrl', 'alt'], () =>
    setAbsoluteFrame(getAbsolutePosition('top-half'))),
  bottom_half: new Key('down', ['ctrl', 'alt'], () =>
    setAbsoluteFrame(getAbsolutePosition('bottom-half'))),

  // maximize
  maximize: new Key('m', ['ctrl', 'alt'], () =>
    Window.focused().maximize()),

  // thirds
  t1: new Key('1', ['ctrl', 'alt'], () =>
    setFrame(getPosition('left-third'))),
  t2: new Key('2', ['ctrl', 'alt'], () =>
    setFrame(getPosition('center-third'))),
  t3: new Key('3', ['ctrl', 'alt'], () =>
    setFrame(getPosition('right-third'))),

  // move window between screens
  leftScreen: new Key('left', ['ctrl', 'alt', 'cmd'], () =>
    moveToScreen({ offset: 1 })),
  rightScreen: new Key('right', ['ctrl', 'alt', 'cmd'], () =>
    moveToScreen({ offset: -1 })),
};
