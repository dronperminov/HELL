function Swipe(element, removeBlock, canSwipe = true, swipePart = 0.6) {
    this.element = element
    this.removeBlock = removeBlock
    this.canSwipe = canSwipe
    this.swipePart = swipePart
    this.isStarted = false

    this.element.addEventListener('touchstart', (e) => this.TouchStart(e))
    this.element.addEventListener('touchend', (e) => this.TouchEnd(e))
    this.element.addEventListener('touchmove', (e) => this.TouchMove(e))
    this.element.addEventListener('transitionend', () => this.Swipe())

    this.onStart = () => {}
    this.onSwipe = () => {}
    this.onPress = () => {}
}

Swipe.prototype.Swipe = function() {
    if (this.element.style.transform.match(/^translateX\(0(px)?\)$/g))
        return

    this.onSwipe()
}

Swipe.prototype.TouchStart = function(e) {
    this.startX = e.touches[0].clientX
    this.startY = e.touches[0].clientY
    this.element.classList.remove('swipe-animated')
    this.pressTimeout = setTimeout(() => {
        this.onPress()
    }, 500)
}

Swipe.prototype.TouchMove = function(e) {
    this.deltaX = e.touches[0].clientX - this.startX
    this.deltaY = e.touches[0].clientY - this.startY

    if (Math.abs(this.deltaX) < Math.abs(this.deltaY) && !this.isStarted)
        return

    clearTimeout(this.pressTimeout)
    e.preventDefault()

    if (!this.canSwipe)
        return

    if (!this.isStarted) {
        this.onStart()
        this.isStarted = true
    }

    if (this.deltaX > 0)
        this.startX += this.deltaX

    let scale = Math.min(Math.abs(this.deltaX) / (this.element.clientWidth * this.swipePart), 1)

    this.element.style.transform = `translateX(${Math.min(0, this.deltaX)}px)`
    this.removeBlock.style.transition = 'none'
    this.removeBlock.style.opacity = '1'
    this.removeBlock.style.opacity = `${scale * 100}%`
    this.removeBlock.style.width = `${Math.max(0, -this.deltaX)}px`
}

Swipe.prototype.CancelSwipe = function() {
    this.element.style.transform = `translateX(0)`
    this.removeBlock.style.width = `0`
    this.removeBlock.style.opacity = '0'
    this.removeBlock.style.transition = null
    this.isStarted = false
}

Swipe.prototype.TouchEnd = function(e) {
    clearTimeout(this.pressTimeout)

    if (!this.isStarted || !this.canSwipe)
        return

    this.isStarted = false
    this.element.classList.add('swipe-animated')
    let swiped = Math.abs(this.deltaX) > this.element.clientWidth * this.swipePart

    if (!swiped) {
        this.CancelSwipe()
        return
    }

    this.removeBlock.style.transition = null
    this.element.style.transform = `translateX(${-this.element.clientWidth}px)`
    this.removeBlock.style.width = `100%`
}