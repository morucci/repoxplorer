function gen_histo(histo, id) {
    var svg_histo = dimple.newSvg("#"+id, '100%', 250);
    var chart_histo = new dimple.chart(svg_histo, histo);
    chart_histo.addCategoryAxis("x", "date");
    chart_histo.addMeasureAxis("y", "value");
    chart_histo.setMargins("60px", "30px", "60px", "70px");
    chart_histo.addSeries(null, dimple.plot.bar);
    chart_histo.draw();
    $( window ).resize(function() {
        chart_histo.draw(0, true);
    });
}

function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
}

function install_date_pickers() {
    var dfrom = getUrlParameter('dfrom');
    var dto = getUrlParameter('dto');
    $( "#fromdatepicker" ).datepicker();
    $( "#fromdatepicker" ).datepicker('setDate', dfrom);
    $( "#todatepicker" ).datepicker();
    $( "#todatepicker" ).datepicker('setDate', dto);
}

function get_groups(nameonly, prefix) {
    var args = {};
    args['nameonly'] = nameonly;
    args['prefix'] = prefix;
    return $.getJSON("api_groups/", args);
}

function get_histo(pid, tid, cid, gid, type) {
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['gid'] = gid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');
    args['metadata'] = getUrlParameter('metadata');
    args['exc_groups'] = getUrlParameter('exc_groups');
    return $.getJSON("histo/" + type, args);
}

function create_alpha_index(groups) {
    r = {};
    for (group in groups) {
        i = group[0].toLowerCase();
        if (r[i]) {
            r[i]++;
        } else {
            r[i] = 1;
        }
    }
    return r;
}

function projects_page_init() {
    lastfilter = "";
    $('#projects-filter-input').keyup(function(event) {
        if ($('#projects-filter-input').val() != lastfilter) {
            inp=$('#projects-filter-input').val();
            $("div[id^=project-panel-]").each(function(i, el) {
                $(this).hide();
            });
            if (inp != '') {
                $("div[data-repoid*="+inp+"]").each(function(i, el) {
                    repoid=$(this).data("repoid");
                    if (repoid.toLowerCase().indexOf(inp.toLowerCase()) > -1) {
                        $('#project-panel-'+repoid).show();
                    }
                });
            } else {
                $("div:hidden").each(function(i, el) {
                    $(this).show();
                });
            }
        }
        lastfilter = $('#projects-filter-input').val();
    });
}

function groups_page_init() {
    var prefix = getUrlParameter('prefix');
    if (prefix === undefined) {
        prefix = 'a';
    }
    var ggn_d = get_groups(true);
    ggn_d
        .done(function(data) {
            index = create_alpha_index(data);
            $("#groups-index").empty();
            $.each(index, function(i, m) {
                $("#groups-index").append(
                    "<span><a href='groups.html?prefix=" + i + "'>" + i + "(" + m + ") " + "</a></span>");
            });
            console.log(index);
        })
        .fail(function(err) {
            console.log(err);
        });
    var gg_d = get_groups(false, prefix);
    gg_d
        .done(
            function(data) {
                $("#groups-table").empty();
                $("#groups-table").append("<table class=\"table table-striped\">");
                var theader = "<tr>";
                theader += "<th>Group name</th>";
                theader += "<th>Group description</th>";
                theader += "<th>Group members</th>";
                $("#groups-table table").append(theader);
                $.each(data, function(gid, gdata) {
                    var elm = "<tr>";
                    elm += "<td><a href=group.html?gid=" + encodeURIComponent(gid) + ">" + gid + "</a></td>";
                    elm += "<td>" + gdata['description'] + "</td>";
                    elm += "<td>";
                    $.each(gdata['members'], function(cid, cdata) {
                        elm += "<span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                            cdata['gravatar'] + "?s=20&d=wavatar'></span><span style='padding-right: 5px'>" +
                            "<a href=contributor.html?cid=" + cid + ">" + cdata['name'] + "</a></span>";
                    });
                    elm += "</td>";
                    $("#groups-table table").append(elm);
                });
                $("#groups-table").append("</table>");
            })
        .fail(
            function(err) {
                console.log(err);
            });
}

function contributor_page_init(commits_amount) {

    install_date_pickers();

    cid = getUrlParameter('cid');
    pid = getUrlParameter('pid');

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    if (getUrlParameter('inc_repos_detail') == 'on') {
        $('#inc_repos_detail').prop('checked', true);
    }

    $.getJSON("projects.json")
        .done(
            function(data) {
                $('#projects-filter')
                    .find('option')
                    .remove()
                    .end();
                $('#projects-filter').append($('<option>', {
                    text: 'Select a project',
                    value: ''
                }));
                $.each(data['projects'], function(i, o) {
                    $('#projects-filter').append($('<option>', {
                        text: i,
                        value: i
                    }));
                });
                if (getUrlParameter('pid')) {
                    $('#projects-filter').val(getUrlParameter('pid'));
                }
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $("#releasesmodal").on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');

        $.getJSON("projects.json")
            .done(
                function(data) {
                    $('#projects')
                        .find('option')
                        .remove()
                        .end();
                    $('#releases')
                        .find('option')
                        .remove()
                        .end();
                    $('#projects').append($('<option>', {
                        text: 'Select a project',
                        value: ''
                    }));
                    $.each(data['projects'], function(i, o) {
                        $('#projects').append($('<option>', {
                            text: i,
                            value: i
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    }),

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    });

    // Fill the histo commits selector
    var c_h_deferred = get_histo(pid, undefined, cid, undefined, 'commits');
    c_h_deferred
        .done(function(data) {
            gen_histo(data, 'history');
        })
        .fail(function(err) {
            console.log(err);
        });

    install_paginator(pid, undefined, cid, undefined, commits_amount);
    get_commits(pid, undefined, cid, undefined, undefined),

    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });

    $("#filter").click(function(){
        var newlocation = "contributor.html?cid=" + cid;
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#inc_repos_detail').prop('checked')) {
            newlocation = newlocation + "&inc_repos_detail=on";
        }
        if ($('#projects-filter').val() != undefined) {
            newlocation = newlocation + "&pid=" + encodeURIComponent($('#projects-filter').val());
        }
        window.location = newlocation;
    });
}

function group_page_init(commits_amount) {

    install_date_pickers();

    gid = getUrlParameter('gid');
    pid = getUrlParameter('pid');

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    if (getUrlParameter('inc_repos_detail') == 'on') {
        $('#inc_repos_detail').prop('checked', true);
    }

    $.getJSON("projects.json")
        .done(
            function(data) {
                $('#projects-filter')
                    .find('option')
                    .remove()
                    .end();
                $('#projects-filter').append($('<option>', {
                    text: 'Select a project',
                    value: ''
                }));
                $.each(data['projects'], function(i, o) {
                    $('#projects-filter').append($('<option>', {
                        text: i,
                        value: i
                    }));
                });
                if (getUrlParameter('pid')) {
                    $('#projects-filter').val(getUrlParameter('pid'));
                }
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $("#releasesmodal").on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');

        $.getJSON("projects.json")
            .done(
                function(data) {
                    $('#projects')
                        .find('option')
                        .remove()
                        .end();
                    $('#releases')
                        .find('option')
                        .remove()
                        .end();
                    $('#projects').append($('<option>', {
                        text: 'Select a project',
                        value: ''
                    }));
                    $.each(data['projects'], function(i, o) {
                        $('#projects').append($('<option>', {
                            text: i,
                            value: i
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    });

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    })

    // Fill the histo commits selector
    var c_h_deferred = get_histo(pid, undefined, undefined, gid, 'commits');
    c_h_deferred
        .done(function(data) {
            gen_histo(data, 'history');
        })
        .fail(function(err) {
            console.log(err);
        });

    install_paginator(pid, undefined, undefined, gid, commits_amount);
    get_commits(pid, undefined, undefined, gid, undefined),

    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });

    $("#filter").click(function(){
        var newlocation = "group.html?gid=" + gid;
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#inc_repos_detail').prop('checked')) {
            newlocation = newlocation + "&inc_repos_detail=on";
        }
        if ($('#projects-filter').val() != undefined) {
            newlocation = newlocation + "&pid=" + encodeURIComponent($('#projects-filter').val());
        }
        window.location = newlocation;
    });
}

function project_page_init(projectid, tagid) {
    install_date_pickers();

    var selected_metadata = [];

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }

    if (getUrlParameter('inc_repos')) {
        selected = getUrlParameter('inc_repos').split(',');
        $('#repositories').val(selected);
    }

    if (getUrlParameter('metadata')) {
        selected_metadata = getUrlParameter('metadata').split(',');
        $.each(selected_metadata, function(i, v) {
            $("#metadata-selected").append('<span class="badge">'+v+'</div>');
        });
    }

    var newlocation;

    $("#filter").click(function(){
        if (projectid) {
            newlocation = "project.html?pid=" + projectid;
        }
        else {
            newlocation = "project.html?tid=" + tagid;
        }
        if ($('#fromdatepicker').val() != '') {
            newlocation = newlocation + "&dfrom=" + encodeURIComponent($('#fromdatepicker').val());
        }
        if ($('#todatepicker').val() != '') {
            newlocation = newlocation + "&dto=" + encodeURIComponent($('#todatepicker').val());
        }
        if ($('#inc_merge_commit').prop('checked')) {
            newlocation = newlocation + "&inc_merge_commit=on";
        }
        if ($('#repositories').val() != undefined) {
            newlocation = newlocation + "&inc_repos=" + encodeURIComponent($('#repositories').val());
        }
        if ($('#groups').val() != undefined) {
            newlocation = newlocation + "&exc_groups=" + encodeURIComponent($('#groups').val());
        }
        if (selected_metadata.length > 0) {
            newlocation = newlocation + "&metadata=" + encodeURIComponent(selected_metadata.toString());
        }
        window.location = newlocation;
    });

    // Fill the groups selector
    var defer = get_groups(true);
    defer.done(
        function(data) {
            $('#groups')
                .find('option')
                .remove()
                .end();
            $.each(data, function(i, v) {
                $('#groups').append($('<option>', {
                    text: i,
                    value: i
                }));
            });
            if (getUrlParameter('exc_groups')) {
                excluded_groups = getUrlParameter('exc_groups').split(',');
                $('#groups').val(excluded_groups);
            }
        }
    )
        .fail(
            function(err) {
                console.log(err);
            }
        );
    // Fill the histo commits selector
    var defer2 = get_histo(projectid, tagid, undefined, undefined, 'commits');
    defer2
        .done(function(data) {
            gen_histo(data, 'history');
        })
        .fail(function(err) {
            console.log(err);
        });

    // Fill the histo author selector
    var defer3 = get_histo(projectid, tagid, undefined, undefined, 'authors');
    defer3
        .done(function(data) {
            gen_histo(data, 'history_author');
        })
        .fail(function(err) {
            console.log(err);
        });

    $("#add-to-filter").click(function(){
        metadata = $('#metadata').val();
        value = $('#metadata-values').val();
        if (metadata === '') {return 1;}
        selected_metadata.push(metadata + ":" + value);
        $("#metadata-selected").html("");
        $.each(selected_metadata, function(i, v) {
            $("#metadata-selected").append('<span class="badge">'+v+'</div>');
        });
    });

    $("#clean-filter").click(function(){
        selected_metadata = [];
        $("#metadata-selected").html("");
    });

    var pickupdatetarget = undefined;
    $('#releasesmodal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        pickupdatetarget = button.data('datetarget');
    });
    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });
}

function contributors_page_init() {

    function fill_resultinfos(ret) {
        var size = Object.keys(ret).length;
        $("#resultinfos").empty();
        $("#resultinfos").append(" - " + size + " results");
    }
    function fill_result(ret) {
        $("#search-results").empty();
        $.each(ret, function(k, v) {
            var box = '<div class="col-md-2"><div class="panel panel-default">' +
                '<div class="panel-heading"><h3 class="panel-title">' +
                '<span style="padding-right: 5px"><img src="https://www.gravatar.com/avatar/' +
                v.gravatar + '?s=20&d=wavatar"></span>' +
                '<span><a href=contributor.html?cid=' +
                k + '>' + v.name + '</a></span></h3>' +
                '</div></div></div>';
            $("#search-results").append(box);
        });
    }
    $('#search-txt').bind("enterKey",function(e){
        var args = {};
        args['query'] = $("#search-txt").val();
        $.getJSON("search_authors.json", args)
            .done(
                function(data) {
                    fill_resultinfos(data);
                    fill_result(data);
                })
            .fail(
                function(err) {
                });
    });
    $('#search-txt').keyup(function(e){
      if(e.keyCode == 13) {
        $(this).trigger("enterKey");
    }
    });
}

function get_releases(pid, tid) {
    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_repos'] = getUrlParameter('inc_repos');

    var releases = [];
    $.getJSON("tags.json", args)
        .done(
            function(data) {
                data.sort(function(a, b){
                    if(a.date < b.date){ return 1;}
                    if(a.date > b.date){ return -1;}
                    return 0;
                });
                $.each(data, function(i, o) {
                    rdate = new Date(1000 * o.date);
                    rdate = moment(rdate);
                    $('#releases').append($('<option>', {
                        text: rdate.format("YYYY-MM-DD") + " - " + o.name + " - " + o.repo,
                        value: rdate.format("YYYY-MM-DD")
                    }));
                });
            })
        .fail(
            function(err) {
                console.log(err);
            });
}

function get_metadata_keys(pid, tid, cid) {
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }

    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');

    $('#metadata').append($('<option>', {
        text: 'Select a metadata key',
        value: ''
    }));
    $('#metadata-values').append($('<option>', {
        text: 'Select a metadata value',
        value: ''
    }));

    $('#metadata').on('change', function() {
        $('#metadata-values')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        args['key'] = this.value;
        $.getJSON("metadata.json", args)
            .done(
                function(data) {
                    $('#metadata-values').append($('<option>', {
                        text: '*',
                        value: '*'
                    }));
                    $.each(data, function(i, v) {
                        $('#metadata-values').append($('<option>', {
                            text: v,
                            value: v
                        }));
                    });
                })
            .fail(
                function(err) {
                    console.log(err);
                });
    })

    $.getJSON("metadata.json", args)
        .done(
            function(data) {
                var temp = [];
                $.each(data, function(key, value) {
                    temp.push({v:value, k: key});
                });
                temp.sort(function(a, b){
                    if(a.v < b.v){ return 1;}
                    if(a.v > b.v){ return -1;}
                    return 0;
                });
                $.each(temp, function(i, o) {
                    $('#metadata').append($('<option>', {
                        text: o.k + " (" + o.v + " hits)",
                        value: o.k
                    }));
                });
            })
        .fail(
            function(err) {
                console.log(err);
            });
}

function get_commits(pid, tid, cid, gid, page) {
    if (page === undefined) {
        page = 0;
    }
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }

    var args = {};
    args['pid'] = pid;
    args['tid'] = tid;
    args['cid'] = cid;
    args['gid'] = gid;
    args['start'] = page;
    args['dfrom'] = getUrlParameter('dfrom');
    args['dto'] = getUrlParameter('dto');
    args['inc_merge_commit'] = inc_merge_commit;
    args['inc_repos'] = getUrlParameter('inc_repos');
    args['metadata'] = getUrlParameter('metadata');
    args['exc_groups'] = getUrlParameter('exc_groups');

    $.getJSON("commits.json", args).done(function(data) {
        $("#commits-table").empty();
        $("#commits-table").append("<table class=\"table table-striped\">");
        var theader = "<tr>";
        theader += "<th>Date of commit</th>";
        theader += "<th>Repository refs</th>";
        theader += "<th>Author/Committer</th>";
        theader += "<th>Message</th>";
        theader += "<th>Modified lines</th>";
        theader += "<th>Time To Land</th>";
        theader += "</tr>";
        $("#commits-table table").append(theader);
        $.each( data[2], function(k, v) {
            var cmt_date = new Date(1000 * v['committer_date']);
            cmt_date = moment(cmt_date);
            var elm = "<tr>";
            var projects = "";
            $.each(v['repos'], function(i, p) {
                if (i > 0) {projects += "<br>";}
                projects += p;
            });
            elm += "<td>" + cmt_date.format("MMM D, YYYY") + "</td>";
            elm += "<td>" + projects + "</td>";
            elm += "<td><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                v['author_gravatar'] + "?s=20&d=wavatar'></span><span><a href=contributor.html?cid=" +
                v['cid'] + ">" + v['author_name'] + "</a></span>";
            if (v['ccid'] != v['cid']) {
                elm += "<br><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                    v['committer_gravatar'] + "?s=20&d=wavatar'></span><span><a href=contributor.html?cid=" +
                    v['ccid'] + ">" + v['committer_name'] + "</a><span>";
            }
            elm += "</td>";
            // Just use the first gitweb link atm
            if (v['gitwebs'][0].length > 0) {
                elm += "<td><a href=" + v['gitwebs'][0] + ">" + v['commit_msg'] + "</a></td>";
            } else {
                elm += "<td>" + v['commit_msg'] + "</td>";
            }
            elm += "<td>" + v['line_modifieds'] + "</td>";
            elm += "<td>" + v['ttl'] + "</td>";
            elm += "</tr>";
            $("#commits-table table").append(elm);
        });
        $("#commits-table").append("</table>");
    })
        .fail(function(err) {
            console.log(err);
        });
}

function check_fragment() {
    var hash = window.location.hash || "#page-1";
    hash = hash.match(/^#page-(\d+)$/);
    if(hash)
        page = parseInt(hash[1]);
        $("#pagination").pagination('selectPage', page);
}

function install_paginator(pid, tid, cid, gid, items_amount) {
    if (items_amount >= 1000) {
        // Limit the amount of pages to 100
        // User should use the calendar filter to dig in the results
        items_amount = 1000;
    }
    $(window).bind("popstate", check_fragment);
    $(function() {
        $('#pagination').pagination({
            items: items_amount,
            itemsOnPage: 10,
            cssStyle: 'light-theme',
            onPageClick: function(pageNumber, ev) {
                // This check prevent get_commits to be called twice
                if (ev != undefined) {
                    get_commits(pid, tid, cid, gid, (pageNumber - 1) * 10);
                }
            }
        });
        check_fragment();
    });
}
