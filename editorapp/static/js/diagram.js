const svg = d3.select("svg");

const width = document.getElementById("canvas").clientWidth
const height = document.getElementById("canvas").clientHeight
const margin = {top: 25, right: 200, bottom: 25, left: 30}
const innerWidth = width - margin.left - margin.right
const innerHeight = height - margin.top - margin.bottom
const project_name = window.location.pathname.split('/')[2]
const url_string = new URL(`${window.origin}/api`)
url_string.searchParams.append('project', project_name)
url_string.searchParams.append('sgs', true)
url_string.searchParams.append('hgs', true)
url_string.searchParams.append('bbms', true)
// url_string.searchParams.append('assu', true)

const zoomG = svg
    .attr("width", width)
    .attr("height", height)
    .append("g").attr("class", "zoom")

const g = zoomG.append("g")
    .attr("class", "svgContainer")
    .attr("transform", `translate(${margin.left},${margin.top})`)

svg.call(d3.zoom().on("zoom", () => {
    zoomG.attr('transform', d3.event.transform);
}))

d3.json(url_string).then(data => {
    renderTree(data, g);
});

function hoverZoom(d, i) {
    const box = d3.select(this);
    const id = `${this.id}`.replace("box", "name");
    const text = d3.select(`#${id}`)
    const {x, y, width, height} = this.getBBox()
    box.attr("x", x - 2.5)
        .attr("y", y - 2.5)
        .attr("width", width + 5)
        .attr("height", height + 5)
    box.raise()
    text.raise()
}

function hoverOut(d, i) {
    const box = d3.select(this);
    const {x, y, width, height} = this.getBBox()
    box.attr("x", x + 2.5)
        .attr("y", y + 2.5)
        .attr("width", width - 5)
        .attr("height", height - 5)
}

function wrap(text, width) {
    text.each(function() {
        let text = d3.select(this),
            words = text.text().split(/\s+/).reverse(),
            word,
            line = [],
            lineNumber = 0,
            lineHeight = 0.9, // ems
            x = text.attr("x"),
            y = text.attr("y"),
            dy = 1
            tspan = text.text(null).append("tspan").attr("x", x).attr("y", y).attr("dy", dy+"em");
        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(" "));
            if (tspan.node().getComputedTextLength() > width) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = text.append("tspan").attr("x", x).attr("y", y).attr("dy", ++lineNumber*lineHeight + dy + "em")
                    .text(word);
            }
        }
    });
}

function renderTree(data, g) {
    const tree = d3.tree();
    tree.size([innerHeight, innerWidth])

    // tree.nodeSize([50,100])
    // tree.separation((a,b) => a.parent == b.parent ? 1 : 0.5)

    const root = d3.hierarchy(data);

    // Experimental
    root.x0 = innerWidth/2;
    root.y0 = 0;
    root.descendants().forEach((d, i) => {
        d.id = i;
        d._children = d.children;
    })
    // End Experiment

    const links = tree(root).links();
    const linkPathGenerator = d3.linkHorizontal()
        .x(d => d.y)
        .y(d => d.x)

    let left = root;
    let right = root;
    root.eachBefore(node => {
        if(node.x < left.x) left = node;
        if(node.x > right.x) right = node;
    })
    // g.append("g").attr("class", "paths");
    const paths = g.selectAll("path").data(links);

    paths.enter().append("path")
        .merge(paths)
        .attr("d", linkPathGenerator)
        // .attr("class", d => d.source.depth !== 0 ? `path-${d.target.data.status}` : "")
        .attr("class", d => `path-${d.target.data.status}`)
        .attr("stroke", "#959595")
        .lower();

    paths.exit().remove();

    // g.append("g").attr("class", "points");
    const points = g.selectAll("circle").data(root.descendants(), d => d.id);

    // const pointsEnter = points.enter().append("g")
    //     .attr("transform", d => `translate(${data.y0}, ${data.x0})`)
    //     .attr("fill-opacity", 0)
    //     .attr("stroke-opacity", 0)
    //     .on("click", d => {
    //         d.children = d.children ? null : d._children;
    //         renderTree(d, g)
    //     })
    //
    // pointsEnter.append("circle")
    //     .attr("r", 2.5)
    //     .attr("fill", d => d._children ? "#555" : "#999")
    //     .attr("stroke-width", 10)
    //
    // const pointsUpdate = points.merge(pointsEnter)
    //     .attr("transform", d => `translate(${d.y}, ${d.x})`)
    //     .attr("fill-opacity", 1)
    //     .attr("fill-opacity", 1);
    //
    // const pointsExit = points.exit().remove()
    //     .attr("transform", d => `translate(${data.y}, ${data.x})`)
    //     .attr("fill-opacity", 0)
    //     .attr("stroke-opacity", 0)

    points.enter().append("circle")
        .merge(points)
        .attr("class", "node")
        .attr("cx", d => d.y)
        .attr("cy", d => d.x)
        .attr("r", 1.5)

    points.exit().remove();

    // g.append("g").attr("class", "names");
    const names = g.selectAll("text.names").data(root.descendants(), d => d.id);
    const nameBBoxes = []

    names.enter().append("text")
        .raise()
        .merge(names)
        .attr("x", d => d.y + 1.5)
        .attr("y", d => d.x - 5)
        .attr("dy", "0.31em")
        .attr("text-anchor", "start")
        .attr("font-size", d => {
            if(d.depth >= 2) {
                return 1 - (300 * 2 / 1000) + "em"
            } else {
                return 1 - (300 * d.depth / 1000) + "em"
            }
        })
        .attr("class", function(d) {
           if (d.data.desc === 'BBM') {
               return `names n-bbm-${d.data.status}`
           } else {
               if (d.data.original_hg) {
                   return `names n-${d.data.status} e-hg-n`
               } else {
                   return `names n-${d.data.status}`
               }
           }
        })
        .attr("id", (d, i) => `name-${i}`)
        .text(d => d.data.name)
        .call(wrap, innerWidth/6)
        .each(function() {
            nameBBoxes.push(this.getBBox())
        })
        // .on("mouseover", hoverZoom)
        .raise()
        // .on('click', (d) => {
        //     console.log(d)
        //     location.href = `${window.origin}`
        //     console.log(`${window.origin}`)
        // })

    names.exit().remove();

    const descriptions = g.selectAll("text.description").data(root.descendants());
    const bBoxes = []

    descriptions.enter().append("text").attr("class", "description")
        .raise()
        .merge(descriptions)
        .attr("x", d => d.y)
        .attr("y", d => d.x - 5)
        .attr("dy", "0.31em")
        .attr("text-anchor", "end")
        .attr("font-size", "0.29em")
        .attr("class", d => d.data.desc === 'BBM' ? `description d-bbm-${d.data.status}` : `description d-${d.data.status}`)
        .text(d => {
            switch(d.data.desc){
                case "Component":
                case "Soft Goal":
                case "Functional Requirement":
                case "Hard Goal":
                case "BBM":
                    return `(${d.data.status}) ${d.data.desc}`;
                case "Project":
                    return "";
                default:
                    return d.data.desc;
            }
        })
        .each(function() {
            bBoxes.push(this.getBBox())
        })
        .raise()

    descriptions.exit().remove();

    const descBoxes = g.selectAll("rect.desc").data(root.descendants());
    descBoxes.enter().append("rect")
        .merge(descBoxes)
        .attr("x", (d, i) => bBoxes[i].x - 1)
        .attr("rx", 2)
        .attr("ry", 2)
        .attr("y", (d, i) => bBoxes[i].y)
        .attr("width", (d,i) => bBoxes[i].width + 2)
        .attr("height", (d,i) => bBoxes[i].height)
        .attr("fill", "#bbbbbb")
        .attr("name", "desc")
        .attr("class", d => {
            // d.data.desc === 'BBM' ? `desc desc-bbm-${d.data.status}` : `desc desc-${d.data.status}`
            if(d.data.desc === 'BBM') {
                return `desc desc-bbm-${d.data.status}`
            } else if(d.data.desc === 'Assumption') {
                return `desc assu-${d.data.fund}`
            } else {
                return `desc desc-${d.data.status}`
            }
        })
        // .lower();

    descBoxes.exit().remove()

    const nameBoxes = g.selectAll("rect.names").data(root.descendants());
    nameBoxes.enter().append("rect").attr("class", "names")
        .merge(nameBoxes)
        .attr("x", (d, i) => nameBBoxes[i].x - 1)
        .attr("rx", 2)
        .attr("ry", 2)
        .attr("y", (d, i) => nameBBoxes[i].y)
        .attr("width", (d,i) => nameBBoxes[i].width + 2)
        .attr("height", (d,i) => nameBBoxes[i].height)
        .attr("fill", "#bbbbbb")
        .attr("name", "name")
        .attr("id", (d,i) => `box-${i}`)
        .attr("class", d => {
            if(d.data.desc === 'BBM') {
                return `names name-bbm-${d.data.status}`
            } else if(d.data.desc === 'Assumption') {
                return `names assu-${d.data.fund}`
            } else {
                if(d.data.original_hg) {
                    return `names name-${d.data.status} extra-hg`
                } else {
                    return `names name-${d.data.status}`
                }
            }
        })
        .on('mouseover', hoverZoom)
        .on('mouseout', hoverOut)
        .on('click', function(d) {
            if (d.data.extra_hg) {
                window.location.href = `${window.origin}/dendrogram/${project_name}/${d.data.original_hg}`
            }
        })
        // .lower();

    nameBoxes.exit().remove();
    // const descBoxRaiser = g.selectAll("rect.desc").data(root.descendants());
    // const nameBoxRaiser = g.selectAll("names").data(root.descendants());
    const nameRaiser = g.selectAll("text.names").data(root.descendants());
    const descRaiser = g.selectAll("text.description").data(root.descendants());
    nameRaiser.raise()
    descRaiser.raise()

    root.eachBefore(d => {
        d.x0 = d.x;
        d.y0 = d.y;
    })

    // renderTree(data, g)
}

const funcReq = document.getElementById("fr")
const assumptions = document.getElementById("assu")
const actors = document.getElementById("actors")
const softGoals = document.getElementById("sgs")
const assets = document.getElementById("assets")
const stakeholders = document.getElementById("stk")
const attackers = document.getElementById("atk")
const hardGoals = document.getElementById("hgs")
const bbms = document.getElementById("bbms")
const fundamental = document.getElementById("funda")

funcReq.addEventListener("change", (event) => {
    if (event.target.checked) {
        softGoals.checked = true
        if (!url_string.searchParams.has('sgs'))
        {
            url_string.searchParams.append('sgs', true)
        }
        url_string.searchParams.append('fr', true)
        d3.json(url_string).then(data => {
            renderTree(data, g);
        })
    } else {
        url_string.searchParams.delete('fr')
        d3.json(url_string).then(data => {
            renderTree(data, g);
        })
    }
})

actors.addEventListener("change", (event) => {
    if (event.target.checked) {
        url_string.searchParams.append('actors', true)
        d3.json(url_string).then(data => {
            renderTree(data, g);
        })
    } else {
        url_string.searchParams.delete('actors')
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

softGoals.addEventListener("change", (event) => {
    if(event.target.checked) {
        url_string.searchParams.append('sgs', true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        funcReq.checked = false
        assets.checked = false
        hardGoals.checked = false
        bbms.checked = false
        stakeholders.checked = false
        attackers.checked = false
        assumptions.checked = false
        fundamental.checked = false
        url_string.searchParams.delete('fr')
        url_string.searchParams.delete('assets')
        url_string.searchParams.delete('atk')
        url_string.searchParams.delete('hgs')
        url_string.searchParams.delete('bbms')
        url_string.searchParams.delete('assu')
        url_string.searchParams.delete('stk')
        url_string.searchParams.delete('sgs')
        url_string.searchParams.delete('funda')
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

assets.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        if (!url_string.searchParams.has('sgs'))
        {
            url_string.searchParams.append('sgs', true)
        }
        url_string.searchParams.append('assets', true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        url_string.searchParams.delete('assets')
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

stakeholders.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        if (!url_string.searchParams.has('sgs'))
        {
            url_string.searchParams.append('sgs', true)
        }
        url_string.searchParams.append('stk', true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        url_string.searchParams.delete('stk')
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

attackers.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        if (!url_string.searchParams.has('sgs'))
        {
            url_string.searchParams.append('sgs', true)
        }
        url_string.searchParams.append('atk', true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        url_string.searchParams.delete('atk')
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

hardGoals.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        if (!url_string.searchParams.has("sgs")){
            url_string.searchParams.append("sgs", true)
        }
        url_string.searchParams.append("hgs", true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        bbms.checked = false
        assumptions.checked = false
        fundamental.checked = false
        url_string.searchParams.delete("bbms")
        url_string.searchParams.delete("assu")
        url_string.searchParams.delete("hgs")
        url_string.searchParams.delete("funda")
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

bbms.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        hardGoals.checked = true
        if(!url_string.searchParams.has("sgs")){
            url_string.searchParams.append("sgs", true)
        }
        if(!url_string.searchParams.has("hgs")){
            url_string.searchParams.append("hgs", true)
        }
        url_string.searchParams.append("bbms", true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        assumptions.checked = false
        fundamental.checked = false
        url_string.searchParams.delete("bbms")
        url_string.searchParams.delete("assu")
        url_string.searchParams.delete("funda")
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})
assumptions.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        hardGoals.checked = true
        bbms.checked = true
        if(!url_string.searchParams.has("sgs")){
            url_string.searchParams.append("sgs", true)
        }
        if(!url_string.searchParams.has("hgs")){
            url_string.searchParams.append("hgs", true)
        }
        if(!url_string.searchParams.has("bbms")){
            url_string.searchParams.append("bbms", true)
        }
        url_string.searchParams.append("assu", true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        url_string.searchParams.delete("assu")
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})

fundamental.addEventListener("change", (event) => {
    if(event.target.checked) {
        softGoals.checked = true
        hardGoals.checked = true
        bbms.checked = true
        if(!url_string.searchParams.has("sgs")){
            url_string.searchParams.append("sgs", true)
        }
        if(!url_string.searchParams.has("hgs")){
            url_string.searchParams.append("hgs", true)
        }
        if(!url_string.searchParams.has("bbms")){
            url_string.searchParams.append("bbms", true)
        }
        url_string.searchParams.append("funda", true)
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    } else {
        url_string.searchParams.delete("funda")
        d3.json(url_string).then(data => {
            renderTree(data, g)
        })
    }
})