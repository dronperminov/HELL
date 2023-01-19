function BarChart(barClass = 'bar-color', labelClass = 'label', dividerClass = 'bar-divider', padding = 5, topPadding = 18, bottomPadding = 10, minRectWidth=42, maxRectWidth = 60, gap = 2) {
    this.barClass = barClass
    this.labelClass = labelClass
    this.dividerClass = dividerClass

    this.padding = padding
    this.topPadding = topPadding
    this.bottomPadding = bottomPadding
    this.minRectWidth = minRectWidth
    this.maxRectWidth = maxRectWidth
    this.gap = gap
}

BarChart.prototype.GetMaxValue = function(data, key) {
    let max = 0

    for (let dataItem of data)
        max = Math.max(max, dataItem[key])

    return max > 0 ? max : 1
}

BarChart.prototype.MakeLabel = function(x, y, labelText, baseline = "middle") {
    let label = document.createElementNS('http://www.w3.org/2000/svg', "text")
    label.textContent = labelText
    label.setAttribute("x", x)
    label.setAttribute("y", y)
    label.setAttribute("alignment-baseline", baseline)
    label.setAttribute("text-anchor", "middle")
    label.setAttribute("class", this.labelClass)
    return label
}

BarChart.prototype.MakeBar = function(x, y, rectWidth, rectHeight, className) {
    let bar = document.createElementNS('http://www.w3.org/2000/svg', "rect")
    bar.setAttribute("x", x)
    bar.setAttribute("y", y)
    bar.setAttribute("width", rectWidth)
    bar.setAttribute("height", rectHeight)
    bar.setAttribute("class", className)
    return bar
}

BarChart.prototype.MakeDivider = function(x, y, width) {
    let path = document.createElementNS('http://www.w3.org/2000/svg', "path")
    path.setAttribute("d", `M${x} ${y} l${width} 0`)
    path.setAttribute("stroke-width", this.gap)
    path.setAttribute("class", this.dividerClass)
    return path
}

BarChart.prototype.AppendBar = function(svg, x, y, rectWidth, rectHeight, data, keys) {
    if (rectHeight == 0)
        return []

    let coords = []
    let total = 0

    for (let key of keys)
        total += data[key]

    for (let i = 0; i < keys.length; i++) {
        let partHeight = data[keys[i]] / total * rectHeight
        svg.appendChild(this.MakeBar(x, y, rectWidth, partHeight, `${this.barClass}${i + 1}`))

        if (i > 0)
            coords.push(y)

        y += partHeight
    }

    for (let coord of coords)
        svg.appendChild(this.MakeDivider(x, coord, rectWidth))
}

BarChart.prototype.Plot = function(svg, data, keys, axisKey, labelKey, labelUnit) {
    let width = svg.clientWidth
    let height = svg.clientHeight
    let rectWidth = width / data.length - this.padding
    let maxValue = this.GetMaxValue(data, labelKey)

    if (rectWidth < this.minRectWidth) {
        rectWidth = this.minRectWidth
        width = (rectWidth + this.padding) * data.length
        svg.style.width = `${width}px`
    }
    else if (rectWidth > this.maxRectWidth) {
        rectWidth = this.maxRectWidth
    }

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`)

    for (let i = 0; i < data.length; i++) {
        let rectHeight = data[i][labelKey] / maxValue * (height - this.topPadding - this.bottomPadding)
        let x = this.padding / 2 + i * (this.padding + rectWidth)
        let y = height - this.bottomPadding - rectHeight

        this.AppendBar(svg, x, y, rectWidth, rectHeight, data[i], keys)

        svg.appendChild(this.MakeLabel(x + rectWidth / 2, height - this.bottomPadding / 2, data[i][axisKey]))
        svg.appendChild(this.MakeLabel(x + rectWidth / 2, y - 8, `${data[i][labelKey]}`, "top"))
        svg.appendChild(this.MakeLabel(x + rectWidth / 2, y - 2, labelUnit, "top"))
    }
}