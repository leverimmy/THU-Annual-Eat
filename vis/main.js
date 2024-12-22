function h(tag, props, children = []) {
  const elem = document.createElement(tag);
  for (const key in props) {
    if (key === "style") {
      Object.assign(elem.style, props[key]);
    } else if (key === "dataset") {
      Object.assign(elem.dataset, props[key]);
    } else if (key.startsWith("on")) {
      elem.addEventListener(key.slice(2).toLowerCase(), props[key]);
    } else {
      elem.setAttribute(key, props[key]);
    }
  }
  for (const child of children) {
    if (typeof child === "string") {
      elem.appendChild(document.createTextNode(child));
    } else if (child) {
      elem.appendChild(child);
    } else {
      elem.appendChild(document.createElement("br"));
    }
  }
  return elem;
}

const xmlns = "http://www.w3.org/2000/xmlns/";
const xlinkns = "http://www.w3.org/1999/xlink";
const svgns = "http://www.w3.org/2000/svg";
// serialize svg to blob
function serialize(svg) {
  svg = svg.cloneNode(true);
  const fragment = window.location.href + "#";
  const walker = document.createTreeWalker(svg, NodeFilter.SHOW_ELEMENT);
  while (walker.nextNode()) {
    for (const attr of walker.currentNode.attributes) {
      if (attr.value.includes(fragment)) {
        attr.value = attr.value.replace(fragment, "#");
      }
    }
  }
  svg.setAttributeNS(xmlns, "xmlns", svgns);
  svg.setAttributeNS(xmlns, "xmlns:xlink", xlinkns);
  const serializer = new window.XMLSerializer();
  const string = serializer.serializeToString(svg);
  return new Blob([string], { type: "image/svg+xml" });
}
function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = h("a", {
    href: url,
    download: filename,
  });
  a.click();
  URL.revokeObjectURL(url);
}
function buttonsToSave(svg) {
  const saveAsSvg = h(
    "button",
    {
      onclick: () => {
        const blob = serialize(svg);
        saveBlob(blob, "plot.svg");
      },
    },
    ["保存成 SVG"]
  );
  return saveAsSvg;
}
function putPlot(sel, plot) {
  d3.select(sel).select("figure").remove();
  d3.select(sel).node().appendChild(plot);
  d3.select(sel).node().appendChild(buttonsToSave(plot));
}
const mformat = d3.format(".2f");
const addDate = (x) => new Date(new Date("2024-01-01").setDate(x));

const output = aq
  .from(
    raw.map((x) => ({
      ...x,
      date: new Date(x.date),
      value: x.value / 100,
      balance: x.balance / 100,
    }))
  )
  .derive({
    day: (d) => op.dayofyear(d.date),
    time: (d) =>
      op.hours(d.date) * 60 + op.minutes(d.date) + op.seconds(d.date) / 60,
  });
output.print();
const totalValue = [...output.rollup({ total: (d) => op.sum(d.value) })][0]
  .total;
d3.select("#ntot").text(mformat(totalValue));
const nameData = [
  ...output
    .groupby("name")
    .rollup({ total: (d) => op.sum(d.value) })
    .orderby(aq.desc("total")),
];
d3.select("#nwindow").text(nameData[0].name);
const placeData = [
  ...output
    .groupby("place")
    .rollup({ total: (d) => op.sum(d.value) })
    .orderby(aq.desc("total")),
];
d3.select("#nplace").text(placeData[0].place);
putPlot(
  "#pwindow",
  Plot.plot({
    title: "「各窗口消费额分布图」",
    marginLeft: 150,
    color: { legend: true },
    y: {
      label: "食堂窗口",
      domain: nameData.map((x) => x.name),
    },
    x: {
      label: "💴",
    },
    marks: [
      Plot.barX(nameData, {
        x: "total",
        y: "name",
        fill: "total",
        tip: true,
      }),
      Plot.ruleX([0]),
    ],
  })
);
putPlot(
  "#pplace",
  Plot.plot({
    title: "「各食堂消费额分布图」",
    marginLeft: 150,
    color: { legend: true },
    y: {
      label: "食堂",
      domain: placeData.map((x) => x.place),
    },
    x: {
      label: "💴",
    },
    marks: [
      Plot.barX(placeData, {
        x: "total",
        y: "place",
        fill: "total",
        tip: true,
      }),
      Plot.ruleX([0]),
    ],
  })
);
const totals = output.groupby("day").rollup({ total: (d) => op.sum(d.value) });
const daystats = [
  ...totals.rollup({
    avg_value: (d) => op.mean(d.total),
    mid_value: (d) => op.median(d.total),
    count: (d) => d.count(),
  }),
][0];
d3.select("#ndaycount").text(daystats.count);
d3.select("#ndayavg").text(mformat(daystats.avg_value));
d3.select("#ndaymid").text(mformat(daystats.mid_value));
const days = aq.table({
  day: Array(365)
    .fill(0)
    .map((_, i) => i + 1),
});
const dateData = [
  ...days.lookup(totals, "day", "total").impute({ total: () => 0 }),
];
putPlot(
  "#pyear",
  Plot.plot({
    title: "「每日消费额折线图」",
    x: {
      label: "日期",
      transform: addDate,
      domain: [new Date("2024-01-01"), new Date("2024-12-31")],
    },
    y: {
      label: "总消费",
    },
    marks: [
      Plot.dot(
        dateData.filter((d) => d.total >= 0.01),
        { x: "day", y: "total", stroke: "#cccccc", tip: true }
      ),
      Plot.line(
        dateData,
        Plot.windowY(14, { x: "day", y: "total", stroke: "#ff8738" })
      ),
    ],
  })
);
