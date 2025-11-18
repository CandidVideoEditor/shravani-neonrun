// A compact Phaser 3 scene with placeholders for high-quality art and sound.
// Replace assets in /static/assets and update paths if you add more.

const config = {
  type: Phaser.AUTO,
  parent: 'game-container',
  width: 960,
  height: 600,
  backgroundColor: '#0b0f1a',
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: 600 }, debug: false }
  },
  scene: {
    preload: preload,
    create: create,
    update: update
  }
};

let player, cursors, stars, score = 0, scoreText;

function preload() {
  // Placeholder images/sounds — replace with high-quality assets
  this.load.image('bg', '/static/assets/placeholder.png');
  this.load.image('platform', '/static/assets/placeholder.png');
  this.load.image('star', '/static/assets/placeholder.png');
  this.load.spritesheet('player', '/static/assets/placeholder.png', { frameWidth: 48, frameHeight: 48 });
  this.load.audio('hit', '/static/assets/placeholder_sound.mp3');
}

function create() {
  // background
  this.add.image(480, 300, 'bg').setScale(3);

  // platforms
  const platforms = this.physics.add.staticGroup();
  platforms.create(480, 584, 'platform').setScale(3,0.5).refreshBody();

  // player
  player = this.physics.add.sprite(100, 450, 'player');
  player.setBounce(0.2);
  player.setCollideWorldBounds(true);

  // animations (placeholder)
  this.anims.create({
    key: 'left',
    frames: this.anims.generateFrameNumbers('player', { start: 0, end: 0 }),
    frameRate: 10,
    repeat: -1
  });

  // stars
  stars = this.physics.add.group({
    key: 'star',
    repeat: 11,
    setXY: { x: 12, y: 0, stepX: 80 }
  });
  stars.children.iterate(function (child) {
    child.setBounceY(Phaser.Math.FloatBetween(0.4, 0.8));
  });

  // collisions
  this.physics.add.collider(player, platforms);
  this.physics.add.collider(stars, platforms);

  // overlaps
  this.physics.add.overlap(player, stars, collectStar, null, this);

  // input
  cursors = this.input.keyboard.createCursorKeys();

  // score
  scoreText = this.add.text(16, 16, 'Score: 0', { fontSize: '28px', fill: '#fff' });

  // show username
  let u = (window.APP && window.APP.user && window.APP.user.username) ? window.APP.user.username : 'Guest';
  this.add.text(650, 16, `Player: ${u}`, { fontSize: '18px', fill: '#fff' });

  // a little sound
  this.sound.add('hit');
}

function update() {
  if (!cursors) return;
  if (cursors.left.isDown) {
    player.setVelocityX(-200);
    player.anims.play('left', true);
  } else if (cursors.right.isDown) {
    player.setVelocityX(200);
    player.anims.play('left', true);
  } else {
    player.setVelocityX(0);
    player.anims.stop();
  }

  if (cursors.up.isDown && player.body.touching.down) {
    player.setVelocityY(-400);
  }
}

function collectStar(player, star) {
  star.disableBody(true, true);
  score += 10;
  scoreText.setText('Score: ' + score);
  this.sound.play('hit');

  if (stars.countActive(true) === 0) {
    // respawn
    stars.children.iterate(function (child) {
      child.enableBody(true, child.x, 0, true, true);
    });
  }
}

const game = new Phaser.Game(config);
