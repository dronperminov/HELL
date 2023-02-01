function SwipeTabs(container, header) {
    this.container = container
    this.header = header
    this.tabs = container.children.length
    this.tab = 0

    this.container.addEventListener("touchstart", (e) => this.TouchStart(e))
    this.container.addEventListener("touchmove", (e) => this.TouchMove(e))
    this.container.addEventListener("touchend", (e) => this.TouchEnd(e))
    this.container.addEventListener("transitionend", () => this.TransitionEnd())

    for (let i = 0; i < this.tabs; i++)
        header.children[i].addEventListener("click", () => this.ChangeTab(i))

    this.UpdateParams()
}

SwipeTabs.prototype.UpdateHeader = function(tab) {
    for (let i = 0; i < this.tabs; i++)
        this.header.children[i].classList.remove("active")

    this.header.children[tab].classList.add("active")
    this.header.scrollLeft = this.header.children[tab].offsetLeft - 10
}

SwipeTabs.prototype.UpdateParams = function() {
    this.container.style.transform = `translateX(${-this.tab * this.container.clientWidth}px)`
    this.container.style.height = `${this.container.children[this.tab].clientHeight}px`
    this.UpdateHeader(this.tab)
}

SwipeTabs.prototype.TouchStart = function(e) {
    this.startX = e.touches[0].clientX
    this.startY = e.touches[0].clientY
    this.container.style.transition = null
}

SwipeTabs.prototype.TouchMove = function(e) {
    let deltaX = e.touches[0].clientX - this.startX
    let deltaY = e.touches[0].clientY - this.startY

    if (Math.abs(deltaX) < Math.abs(deltaY) * 2 && !this.isStarted)
        return

    e.preventDefault()

    this.isStarted = true
    let offset = this.tab * this.container.clientWidth - deltaX

    if (offset < 0)
        this.startX += deltaX

    offset = Math.max(0, Math.min(this.container.clientWidth * (this.tabs - 1), offset))
    this.part = Math.min(offset / this.container.clientWidth, this.tabs - 1)

    this.container.style.transform = `translateX(${-offset}px)`

    let tab = Math.round(this.part) == this.tab ? this.tab : this.tab - Math.sign(deltaX)
    this.container.style.transition = 'height 0.3s'
    this.container.style.height = `${this.container.children[Math.max(0, Math.min(this.tabs - 1, tab))].clientHeight}px`

    this.UpdateHeader(Math.round(this.part))
}

SwipeTabs.prototype.TouchEnd = function(e) {
    this.isStarted = false
    this.ChangeTab(Math.round(this.part))
}

SwipeTabs.prototype.TransitionEnd = function() {
    this.container.style.transition = null
}

SwipeTabs.prototype.ChangeTab = function(tab) {
    this.tab = tab
    this.container.style.transition = 'transform 0.15s, height 0.15s'
    this.UpdateParams()
}