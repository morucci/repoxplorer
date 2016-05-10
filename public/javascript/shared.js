function gen_histo(histo) {
  var svg_histo = dimple.newSvg("#history", 800, 350);
  var chart_histo = new dimple.chart(svg_histo, histo);
  chart_histo.addCategoryAxis("x", "date");
  chart_histo.addMeasureAxis("y", "value");
  chart_histo.setBounds(30, 30, 750, 250);
  chart_histo.addSeries(null, dimple.plot.bar);
  chart_histo.draw();
}

function gen_top_author_pie(pie_top) {
  var svg_pie_top = dimple.newSvg("#topauthors_pie", 590, 400);
  var chart_pie_top = new dimple.chart(svg_pie_top, pie_top);
  chart_pie_top.setBounds(20, 20, 400, 340)
  chart_pie_top.addMeasureAxis("p", "amount");
  chart_pie_top.addSeries("name", dimple.plot.pie);
  chart_pie_top.addLegend(500, 20, 90, 300, "right");
  chart_pie_top.draw();
}

function gen_top_author_modified_pie(pie_top_m) {
  var svg_pie_top_m = dimple.newSvg("#topauthors_m_pie", 590, 400);
  var chart_pie_top_m = new dimple.chart(svg_pie_top_m, pie_top_m);
  chart_pie_top_m.setBounds(20, 20, 400, 340)
  chart_pie_top_m.addMeasureAxis("p", "amount");
  chart_pie_top_m.addSeries("name", dimple.plot.pie);
  chart_pie_top_m.addLegend(500, 20, 90, 300, "right");
  chart_pie_top_m.draw();
}

function install_date_pickers(projectid) {
 $(function() {
   $( "#fromdatepicker" ).datepicker();
   $( "#todatepicker" ).datepicker();
 });

 $("#filter").click(function(){
  var newlocation = "project.html?pid=" + projectid
  if ($('#fromdatepicker').val() != '') {
    newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val())
  }
  if ($('#todatepicker').val() != '') {
    newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val())
  }
  window.location = newlocation
  });
}
