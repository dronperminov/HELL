function Chart(radius = 25, size = 25, gap=2, initAngle = -45) {
    this.radius = radius
    this.size = size
    this.gap = gap
    this.initAngle = initAngle
}

Chart.prototype.GetAngles = function(values) {
    let sum = 0

    for (let value of values)
        sum += value

    let angles = []
    for (let i = 0; i < values.length; i++)
        angles.push((i > 0 ? angles[i - 1] : 0) + values[i] / sum * 2 * Math.PI)

    return angles
}

Chart.prototype.MakeSegment = function(svg, startAngle, endAngle, className) {
    let circle = document.createElementNS('http://www.w3.org/2000/svg', "circle")
    let radius = this.radius + this.size / 2

    circle.setAttribute("cx", 0)
    circle.setAttribute("cy", 0)
    circle.setAttribute("r", radius)

    circle.setAttribute("class", className)
    circle.setAttribute("stroke-width", this.size)
    circle.setAttribute("fill", "none")
    circle.setAttribute("stroke-dasharray", `${radius * (endAngle - startAngle)}, ${radius * 2 * Math.PI}`)
    circle.setAttribute("transform", `rotate(${(startAngle) / Math.PI * 180 + this.initAngle})`)
    svg.appendChild(circle)
}

Chart.prototype.MakeDivider = function(svg, startAngle, endAngle, className) {
    if (endAngle >= Math.PI * 2)
        endAngle = 0

    if (startAngle == endAngle)
        return

    let path = document.createElementNS('http://www.w3.org/2000/svg', "path")
    let angle = endAngle + this.initAngle / 180 * Math.PI

    let x1 = this.radius * Math.cos(angle)
    let y1 = this.radius * Math.sin(angle)

    let x2 = (this.radius + this.size) * Math.cos(angle)
    let y2 = (this.radius + this.size) * Math.sin(angle)

    path.setAttribute("class", className)
    path.setAttribute("stroke-width", this.gap)
    path.setAttribute("d", `M${x1} ${y1} L${x2} ${y2}`)
    svg.appendChild(path)
}

Chart.prototype.Plot = function(svg, values) {
    let angles = this.GetAngles(values)

    for (let i = 0; i < angles.length; i++)
        this.MakeSegment(svg, i > 0 ? angles[i - 1] : 0, angles[i], `chart-color${i + 1}`)

    for (let i = 0; i < angles.length; i++)
        this.MakeDivider(svg, i > 0 ? angles[i - 1] : 0, angles[i], `chart-devider`)
}