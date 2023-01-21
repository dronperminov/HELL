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

function MakeFoodItem(data, resultsDiv, portionClick, portionAdd, isPortionOpen = false) {
    let foodItem = MakeDiv("food-item", resultsDiv, {"id": data.id})

    if ("unit" in data && "size" in data) {
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

    if ("unit" in data && "size" in data) {
        scale = data.size * data.conversions[data.unit]
        energyText = `<span class="food-energy-span">${data.energy * scale}</span> ккал (<span class="food-size-span">${data.size}</span> <span class="food-unit-span">${data.unit}</span>)`
    }
    else {
        energyText = `<span class="food-energy-span">${data.energy}</span> ккал / ${data.portion}`
    }

    let foodEnergy = MakeDiv("food-info-cell food-energy", foodInfo, {
        "innerHTML": energyText, "data-value": data.energy
    })
    MakeDiv("food-info-cell food-proteins", foodInfo, {
        "innerHTML": `Б<span class="food-proteins-span">${Math.round(data.proteins * scale * 100) / 100}</span> г`, "data-value": data.proteins
    })
    MakeDiv("food-info-cell food-fats", foodInfo, {
        "innerHTML": `Ж<span class="food-fats-span">${Math.round(data.fats * scale * 100) / 100}</span> г`, "data-value": data.fats
    })
    MakeDiv("food-info-cell food-carbohydrates", foodInfo, {
        "innerHTML": `У<span class="food-carbohydrates-span">${Math.round(data.carbohydrates * scale * 100) / 100}</span> г`, "data-value": data.carbohydrates
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
    let portionUnitInput = MakeSelect(portionUnit, data.conversions, {
        "id": `${data.id}-portion-unit`,
        "value": data.default_unit
    })

    let portionChange = MakeDiv("food-portion-change", portionControl)
    let icon = MakeIcon(portionChange, "fa fa-plus", () => {
        let size = ValidatePortion(data.id)
        let unit = portionUnitInput.value

        if (size == null)
            return

        portionAdd(data, {size, unit})
    })

    MakeDiv("error-center", portionEdit, {"id": `${data.id}-portion-error`})

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

        console.log(response)
        resultsDiv.innerHTML = ""
        for (let foodItem of response)
            MakeFoodItem(foodItem, resultsDiv, portionClick, portionAdd)
    })
}