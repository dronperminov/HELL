function ClearQuery() {
    let query = document.getElementById("food-query")
    let clear = document.getElementById("food-query-clear")
    let results = document.getElementById("food-search-results")
    query.value = ""
    clear.classList.remove("food-search-clear-show")
    results.innerHTML = ""
}

function UpdateClearQuery() {
    let query = document.getElementById("food-query")
    let clear = document.getElementById("food-query-clear")

    if (query.value.trim().length > 0)
        clear.classList.add("food-search-clear-show")
    else
        clear.classList.remove("food-search-clear-show")
}

function EndEditPortions(ignoreEdit = null) {
    let foodEdits = document.getElementsByClassName('food-portion-edit')

    for (let foodEdit of foodEdits) {
        foodEdit.getElementsByClassName("error-center")[0].innerHTML = ""

        if (foodEdit === ignoreEdit)
            continue

        foodEdit.classList.add('no-display')
        foodEdit.parentNode.classList.remove('food-item-colored')
    }
}

function UpdatePortionInfo(foodId) {
    let sizeInput = document.getElementById(`${foodId}-portion-size`)
    let unitInput = document.getElementById(`${foodId}-portion-unit`)
    let portionError = document.getElementById(`${foodId}-portion-error`)

    let size = sizeInput.value
    let scale

    if (unitInput === null) {
        scale = +size
    }
    else {
        let unit = unitInput.value
        let conversions = {}

        for (let option of unitInput.children)
            conversions[option.getAttribute("value")] = +option.getAttribute("data-value")

        scale = +size * conversions[unit]
    }

    if (!IsPositiveReal(size)) {
        portionError.innerText = "Размер порции введён некорректно"
        sizeInput.classList.add("error")
        scale = 0
    }
    else {
        sizeInput.classList.remove("error")
        portionError.innerText = ""
    }

    for (let key of ["energy", "proteins", "fats", "carbohydrates"]) {
        let value = document.getElementById(`${foodId}-food-${key}`).innerText
        let span = document.getElementById(`${foodId}-food-portion-${key}`)
        span.innerText = `${Math.floor(+value * scale * 10) / 10}`
    }

    let portion = document.getElementById(`${foodId}-food-portion-portion`)

    if (portion === null)
        return

    if (scale > 0) {
        portion.innerText = `/ ${size}`

        if (unitInput !== null)
            portion.innerText += ` ${unitInput.value}`
    }
    else {
        portion.innerText = ""
    }
}

function TogglePortionEdit(id) {
    let foodItem = document.getElementById(id)
    let portionEdit = foodItem.getElementsByClassName('food-portion-edit')[0]
    EndEditPortions(portionEdit)
    portionEdit.classList.toggle('no-display')
    foodItem.classList.toggle('food-item-colored')

    let portionUnit = document.getElementById(`${id}-portion-unit`)

    if (portionUnit !== null)
        portionUnit.value = portionEdit.getAttribute("data-default-unit")

    let portionSize = document.getElementById(`${id}-portion-size`)
    portionSize.value = portionEdit.getAttribute("data-default-value")
    portionSize.focus()
    portionSize.select()
}

function ValidatePortion(id) {
    let portionSize = document.getElementById(`${id}-portion-size`)
    let portionError = document.getElementById(`${id}-portion-error`)

    if (!IsPositiveReal(portionSize.value)) {
        portionSize.focus()
        portionSize.select()
        portionError.innerText = "Размер порции введён некорректно"
        return null
    }

    portionError.innerText = ""
    return portionSize.value
}

function MakeFoodItemSelect(parent, conversions, attributes = null) {
    let select = document.createElement("select")
    let portion = "мл" in conversions && Math.abs(conversions["мл"] - 0.01) < 0.0001 ? "мл" : "г"
    SetAttributes(select, attributes)

    for (let key of Object.keys(conversions)) {
        let option = document.createElement("option")
        option.value = key
        option.innerText = key

        if (key != "г" && key != "мл")
            option.innerText += ` (${Math.round(conversions[key] * 1000) / 10} ${portion})`
        option.setAttribute("data-value", conversions[key])

        if (attributes !== null && attributes.value == key)
            option.setAttribute("selected", "")
        select.appendChild(option)
    }

    parent.appendChild(select)

    return select
}

function MakeFoodItem(data, resultsDiv, portionClick, portionAdd, isPortionOpen = false) {
    let foodItem = MakeDiv("food-item", resultsDiv, {"id": data.id})
    let withPortion = "unit" in data && "size" in data

    if (withPortion) {
        let foodRemove = MakeDiv("food-item-remove", foodItem, {"style": "opacity: 0"})
        let foodRemoveCell = MakeDiv("food-item-remove-cell", foodRemove, {"innerHTML": '<span class="fa fa-trash"></span>'})
    }

    let foodData = MakeDiv("food-data", foodItem)
    let foodName = MakeDiv("food-name", foodData, {"innerText": data.name})
    let foodDescription = MakeDiv("food-description", foodData, {"innerText": data.description})
    let foodInfo = MakeDiv("food-info", foodData)

    foodData.addEventListener("click", () => portionClick(data.id))

    let energyText = ""
    let scale = 1

    if (withPortion) {
        scale = data.size * data.conversions[data.unit]
        energyText = `<span class="food-energy-span" id="${data.id}-food-energy">${Math.round(data.energy * scale * 100) / 100}</span> ккал (<span class="food-size-span">${data.size}</span> <span class="food-unit-span">${data.unit}</span>)`
    }
    else {
        energyText = `<span class="food-energy-span" id="${data.id}-food-energy">${data.energy}</span> ккал / ${data.portion}`
    }

    let foodEnergy = MakeDiv("food-info-cell food-energy", foodInfo, {
        "innerHTML": energyText, "data-value": data.energy
    })
    MakeDiv("food-info-cell food-proteins", foodInfo, {
        "innerHTML": `Б <span class="food-proteins-span" id="${data.id}-food-proteins">${Math.round(data.proteins * scale * 100) / 100}</span>г`, "data-value": data.proteins
    })
    MakeDiv("food-info-cell food-fats", foodInfo, {
        "innerHTML": `Ж <span class="food-fats-span" id="${data.id}-food-fats">${Math.round(data.fats * scale * 100) / 100}</span>г`, "data-value": data.fats
    })
    MakeDiv("food-info-cell food-carbohydrates", foodInfo, {
        "innerHTML": `У <span class="food-carbohydrates-span" id="${data.id}-food-carbohydrates">${Math.round(data.carbohydrates * scale * 100) / 100}</span>г`, "data-value": data.carbohydrates
    })

    let portionEdit = MakeDiv(`food-portion-edit${isPortionOpen ? "" : " no-display"}`, foodItem, {
        "data-default-unit": data.default_unit,
        "data-default-value": data.default_value
    })
    MakeDiv("food-portion-text", portionEdit, {"innerText": "Редактирование порции"})

    let portionControl = MakeDiv("food-portion-control", portionEdit)

    let portionSize = MakeDiv("food-portion-size", portionControl)
    let portionSizeInput = MakeInput("number", portionSize, {
        "id": `${data.id}-portion-size`,
        "value": data.default_value
    })

    let portionUnit = MakeDiv("food-portion-unit", portionControl)
    let portionUnitInput = MakeFoodItemSelect(portionUnit, data.conversions, {
        "id": `${data.id}-portion-unit`,
        "value": data.default_unit
    })

    if (!withPortion) {
        portionSizeInput.addEventListener("input", () => UpdatePortionInfo(data.id))
        portionUnitInput.addEventListener("change", () => UpdatePortionInfo(data.id))
    }

    let portionChange = MakeDiv("food-portion-change", portionControl)
    let icon = MakeIcon(portionChange, withPortion ? "fa fa-check" : "fa fa-plus", () => {
        let size = ValidatePortion(data.id)
        let unit = portionUnitInput.value

        if (size == null)
            return

        portionAdd(data, {size, unit})
    })

    MakeDiv("error-center", portionEdit, {"id": `${data.id}-portion-error`})

    if (!withPortion) {
        let portionInfo = MakeDiv("food-portion-info", portionEdit)

        for (let key of ["energy", "proteins", "fats", "carbohydrates"]) {
            let before = {"energy": "", "proteins": "Б ", "fats": "Ж ", "carbohydrates": "У "}[key]
            let after = {"energy": " ккал", "proteins": "г", "fats": "г", "carbohydrates": "г"}[key]
            let portionInfoCell = MakeDiv(`food-portion-info-cell food-portion-${key}`, portionInfo)

            MakeDiv("", portionInfoCell, {"innerText": before}, "span")
            MakeDiv("", portionInfoCell, {
                "id": `${data.id}-food-portion-${key}`,
                "innerText": `${0}`
            }, "span")
            MakeDiv("", portionInfoCell, {"innerText": after}, "span")

            if (key != "energy")
                continue

            MakeDiv("", portionInfoCell, {
                "id": `${data.id}-food-portion-portion`,
                "innerText": `/ 0`
            }, "span")
        }

        UpdatePortionInfo(data.id)
    }

    return foodItem
}

function SearchFood(portionClick, portionAdd) {
    let queryDiv = document.getElementById("food-query")
    let query = queryDiv.value.trim()
    queryDiv.value = query
    UpdateClearQuery()

    let resultsDiv = document.getElementById("food-search-results")
    resultsDiv.classList.remove("error-center")

    if (!IsNotEmptyValue(query)) {
        resultsDiv.classList.add("error-center")
        resultsDiv.innerHTML = `Введён пустой запрос`
        return
    }

    SendRequest("/food-collection", {food_query: query}).then((response) => {
        if (response.length == 0) {
            resultsDiv.innerHTML = `По запросу <i>"${query}"</i> продуктов не найдено...`
            return
        }

        resultsDiv.innerHTML = ""
        for (let foodItem of response)
            MakeFoodItem(foodItem, resultsDiv, portionClick, portionAdd)
    })
}