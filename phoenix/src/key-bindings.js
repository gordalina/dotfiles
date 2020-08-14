const handles = {
  // window position in screen
  left: new Key('left', ['ctrl', 'option'], () =>
    setFrame(getPosition('left'))),
  right: new Key('right', ['ctrl', 'option'], () =>
    setFrame(getPosition('right'))),

  // halve the window height
  top_half: new Key('up', ['ctrl', 'option'], () =>
    setAbsoluteFrame(getAbsolutePosition('top-half'))),
  bottom_half: new Key('down', ['ctrl', 'option'], () =>
    setAbsoluteFrame(getAbsolutePosition('bottom-half'))),

  // maximize
  maximize: new Key('m', ['ctrl', 'option'], () =>
    Window.focused().maximize()),

  // thirds
  t1: new Key('forwardDelete', ['ctrl', 'option'], () =>
    setFrame(getPosition('left-third'))),
  t2: new Key('end', ['ctrl', 'option'], () =>
    setFrame(getPosition('center-third'))),
  t3: new Key('pageDown', ['ctrl', 'option'], () =>
    setFrame(getPosition('right-third'))),

  // move window between screens
  leftScreen: new Key('left', ['ctrl', 'option', 'cmd'], () =>
    moveToScreen({ offset: -1 })),
  rightScreen: new Key('right', ['ctrl', 'option', 'cmd'], () =>
    moveToScreen({ offset: 1 })),
};
