const handles = {
  // window position in screen
  left: new Key('left', [ 'ctrl', 'alt' ], () => setFrame(getPosition('left'))),
  right: new Key('right', [ 'ctrl', 'alt' ], () => setFrame(getPosition('right'))),
  top: new Key('up', [ 'ctrl', 'alt' ], () => setFrame(getPosition('top'))),
  bottom: new Key('down', [ 'ctrl', 'alt' ], () => setFrame(getPosition('bottom'))),
  maximize: new Key('m', [ 'ctrl', 'alt' ], () => Window.focused().maximize()),

  // move window between screens
  leftScreen: new Key('left', [ 'ctrl', 'alt', 'cmd' ], () => moveToScreen({offset: 1})),
  rightScreen: new Key('right', [ 'ctrl', 'alt', 'cmd' ], () => moveToScreen({offset: -1})),

  // left1: new Key('left', [ 'ctrl', 'alt', 'shift', 'cmd' ], () => setFrame(getPosition('left-1'))),
  // left2: new Key('left', [ 'ctrl', 'alt', 'shift' ], () => setFrame(getPosition('left-2'))),
  //
  // right1: new Key('right', [ 'ctrl', 'alt', 'shift', 'cmd' ], () => setFrame(getPosition('right-1'))),
  // right2: new Key('right', [ 'ctrl', 'alt', 'shift' ], () => setFrame(getPosition('right-2'))),

  bottomLeft: new Key('left', [ 'ctrl', 'alt', 'shift' ], () => setFrame(getRelativePosition('left-thirds'))),
};
