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
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
}

function install_date_pickers() {
    var dfrom = getUrlParameter('dfrom');
    var dto = getUrlParameter('dto');
    $("#fromdatepicker").datepicker(
        {dateFormat: "yy-mm-dd",
         changeMonth: true,
         changeYear: true});
    $("#fromdatepicker").datepicker('setDate', dfrom);
    $("#todatepicker").datepicker(
        {dateFormat: "yy-mm-dd",
         changeMonth: true,
         changeYear: true});
    $("#todatepicker").datepicker('setDate', dto);
}

function get_groups(nameonly, prefix) {
    var args = {};
    args['nameonly'] = nameonly;
    args['prefix'] = prefix;
    return $.getJSON("api/v1/groups", args);
}

function get_histo(pid, tid, cid, gid, type) {
    // TODO: move checkbox value retrieval outside
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
    return $.getJSON("api/v1/histo/" + type, args);
}

function get_top(pid, tid, cid, gid, type, stype) {
    // TODO: move checkbox value retrieval outside
    if ($('#inc_merge_commit').prop('checked')) {
        var inc_merge_commit = 'on';
    }
    if ($('#inc_repos_detail').prop('checked')) {
        var inc_repos_detail = 'true';
    }
    var args = {
        'pid': pid,
        'tid': tid,
        'cid': cid,
        'gid': gid,
        'dfrom': getUrlParameter('dfrom'),
        'dto': getUrlParameter('dto'),
        'inc_merge_commit': inc_merge_commit,
        'inc_repos_detail': inc_repos_detail,
        'inc_repos': getUrlParameter('inc_repos'),
        'metadata': getUrlParameter('metadata'),
        'exc_groups': getUrlParameter('exc_groups')
    };
    return $.getJSON("api/v1/tops/" + type + "/" + stype, args);
}

function fill_info_box(args) {
    $("#infos-repo_refs").empty();
    $("#infos-commits_amount").empty();
    $("#infos-authors_amount").empty();
    $("#infos-duration").empty();
    $("#infos-first_commit").empty();
    $("#infos-last_commit").empty();
    $("#infos-lines_changed").empty();
    $("#infos-author_name").empty();
    $("#infos-gravatar").empty();
    $("#infos-projects_amount").empty();
    $("#infos-repos_amount").empty();
    $("#infos-known_emails").empty();
    $("#infos-description").empty();
    $("#infos-members_amount").empty();

    $("#infos-repo_refs").append('<b>Repository refs:</b> ' + args.repo_refs);
    $("#infos-commits_amount").append('<b>Commits:</b> ' + args.commits_amount);
    $("#infos-authors_amount").append('<b>Authors:</b> ' + args.authors_amount);
    $("#infos-duration").append('<b>Activity duration:</b> ' + args.duration + ' days');
    $("#infos-first_commit").append('<b>Date of first commit:</b> '+ moment(args.first).format("YYYY-MM-DD HH:mm:ss"));
    $("#infos-last_commit").append('<b>Date of last commit:</b> ' + moment(args.last).format("YYYY-MM-DD HH:mm:ss"));
    $("#infos-lines_changed").append('<b>Lines changed:</b> ' + args.line_modifieds_amount);
    $("#infos-author_name").append('<b>Full Name:</b> ' + args.name);
    $("#infos-gravatar").append('<img src="https://www.gravatar.com/avatar/' + args.gravatar + '?s=150" title="' + args.name + '">');
    $("#infos-projects_amount").append('<b>Projects contributed:</b> ' + args.projects_amount);
    $("#infos-repos_amount").append('<b>Repository refs contributed:</b> ' + args.repos_amount);
    $("#infos-known_emails").append('<b>Known emails:</b> ' + args.mails_amount);
    $("#infos-description").append('<b>Description:</b> ' + args.description);
    $("#infos-members_amount").append('<b>Members:</b> ' + args.members_amount);
}

function get_infos(pid, tid, cid, gid) {
    // TODO: move checkbox value retrieval outside
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

    gr_d = $.when();
    gc_d = $.when();
    gg_d = $.when();
    if(pid || tid) {
        gr_d = $.getJSON("api/v1/projects/repos",
                         {'pid': pid, 'tid': tid});
    }
    if(cid) {
        gc_d = $.getJSON("api/v1/infos/contributor", {'cid': cid});
    }
    if (gid) {
        gg_d = $.getJSON("api/v1/groups", args);
    }

    gi_d = $.getJSON("api/v1/infos/infos", args);
    return $.when(gr_d, gi_d, gc_d, gg_d)
        .done(
            function(rdata, idata, cdata, gdata) {
                if (pid || tid) {
                    rdata = rdata[0];
                }
                if (cid) {
                    cdata = cdata[0];
                }
                if (gid) {
                    gdata = gdata[0];
                }
                idata = idata[0];
                var ib_data = {};
                var repo_refs = 0;
                if (pid || tid) {
                    repo_refs = rdata.length;
                }

                ib_data.repo_refs = repo_refs;
                ib_data.duration = parseInt(moment.duration(1000 * idata.duration).asDays());
                ib_data.first = new Date(1000 * idata.first);
                ib_data.last = new Date(1000 * idata.last);
                ib_data.commits_amount = idata.commits_amount;
                ib_data.authors_amount = idata.authors_amount;
                ib_data.line_modifieds_amount = idata.line_modifieds_amount;
                if (cid) {
                    ib_data.name = cdata.name;
                    ib_data.gravatar = cdata.gravatar;
                    ib_data.projects_amount = cdata.projects_amount;
                    ib_data.repos_amount = cdata.repos_amount;
                    ib_data.mails_amount = cdata.mails_amount;
                }
                if (gid) {
                    ib_data.description = gdata[gid].description;
                    var members_amount = 0;
                    var mails_amount = 0;
                    $.each(gdata[gid].members, function(key, value) {
                        members_amount++;
                        mails_amount += value.mails_amount;
                    });
                    ib_data.members_amount = members_amount;
                    ib_data.projects_amount = gdata[gid].projects_amount;
                    ib_data.repos_amount = gdata[gid].repos_amount;
                    ib_data.mails_amount = mails_amount;
                }
                fill_info_box(ib_data);
            })
        .fail(
            function(err) {
                console.log(err);
                if (err.status == 404) {
                    msg = '<string>' + err.responseJSON.message + '</strong>';
                    $("#error-msg").append(msg);
                    $("#error-box").show();
                    $("#infos_filters_div").hide();
                    $("#commits_histo_div").hide();
                    $("#contributors_histo_div").hide();
                    $("#top_authors_c_div").hide();
                    $("#top_authors_lc_div").hide();
                    $("#top_projects_c_div").hide();
                    $("#top_projects_lc_div").hide();
                    $("#commits_listing_div").hide();
                }
            });
}

function create_alpha_index(groups) {
    r = {};
    sr = [];
    for (group in groups) {
        i = group[0].toLowerCase();
        if (r[i]) {
            r[i]++;
        } else {
            r[i] = 1;
        }
    }
    for (k in r) {
        sr.push(k);
    }
    sr.sort();
    return [r, sr];
}

function build_top_authors_head(top, label) {
    top_h = '<div class="row-fluid">';
    for (i = 0; i < top.length; i++) {
        if ( i > 2 ) { break; };
        var pos;
        if (i == 0) { pos = "1 st"; }
        if (i == 1) { pos = "2 nd"; }
        if (i == 2) { pos = "3 rd"; }
        top_h += '<div class="col-md-4">';
        top_h += '<div align="center"><p><b><h3>' + pos + '</h3></b></p></div>';
        top_h += '<div align="center"><p><b><h4>' + top[i].amount + ' ' + label + ' </h4></b></p></div>';
        top_h += '<div align="center"><a href=contributor.html?cid=' + top[i].cid + '>' +
            '<img src="https://www.gravatar.com/avatar/' +
            top[i].gravatar + '?s=150" title=' + top[i].name + '></a></div>';
        top_h += '<div align="center"><p><b><h3><a href=contributor.html?cid=' +
            top[i].cid + '>' + top[i].name + '</a></h3></b></p></div>';
        top_h += '</div>';
    };
    return top_h;
}

function build_top_authors_body(top) {
    top_b = '<table class="table table-striped">';
    top_b += '<tr><th class="col-md-1">Rank</th><th>Name</th><th>Amount</th></tr>';
    for (i = 3; i < top.length; i++) {
        top_b += '<tr>';
        rank = i + 1;
        top_b += '<td>' + rank + '</td>';
        top_b += '<td></span><span style="padding-right: 5px">' +
            '<img src="https://www.gravatar.com/avatar/' +
            top[i].gravatar + '?s=25" title="' + top[i].name + '">' +
            '</span><span><b><a href=contributor.html?cid=' +
            top[i].cid + '>' + top[i].name + '</a></b></span></td>';
        top_b += '<td>' + top[i].amount + '</td>';
        top_b += '</tr>';
    }
    top_b += '</table>';
    return top_b;
}
function build_top_projects_table(top, inc_repos_detail) {
    top_b = '<table class="table table-striped">';
    if (inc_repos_detail == true) {
    top_b += '<tr><th class="col-md-1">Rank</th><th>Project</th><th>Name</th><th>Amount</th></tr>';
    } else {
        top_b += '<tr><th class="col-md-1">Rank</th><th>Name</th><th>Amount</th></tr>';
    }
    for (i = 0; i < top.length; i++) {
        top_b += '<tr>';
        rank = i + 1;
        top_b += '<td>' + rank + '</td>';
        if (inc_repos_detail == true) {
            // A ref can be found in multiple project ... simply use the first item
            top_b += '<td><a href="project.html?pid=' + top[i].projects[0] + '">' + top[i].projects[0] + '</a></td>';
            top_b += '<td><a href="project.html?pid=' + top[i].projects[0] + '&inc_repos=' + top[i].name + '">' + top[i].name +'</a></span> ';
        }
        else {
            top_b += '<td><a href="project.html?pid=' + top[i].name + '">' + top[i].name + '</a></td>';
        }
        top_b += '<td>' + top[i].amount + '</td>';
        top_b += '</tr>';
    }
    top_b += '</table>';
    return top_b;
}

function projects_page_init() {
    function fill_result(data) {
        $("#project-results").empty();
        $("#tag-results").empty();

        var tagoutput = '<div class="col-md-12">';

        if (data['tags'].length > 0) {
            tagoutput += '<div class="panel panel-default">' +
                   '<div class="panel-heading">' +
                   '<h3 class="panel-title text-left"><b>Tags</b></h3>' +
                   '</div>' +
                   '<div class="panel-body">' +
                   '<h4>';
            $.each(data['tags'], function(key, tag) {
                tagoutput +='<a href="project.html?tid=' + tag + '">' + tag + '</a> ';
            });
            tagoutput += '</h4></div></div>';
        }
        tagoutput += '</div>';
        $("#tag-results").append(tagoutput);


        var i;
        projectarray = [];
        $.each(data['projects'], function(k, value) {
            var project_hash = {key: k, value: data['projects'][k]};
            projectarray.push(project_hash);
        });
        var chunk_size =  Math.ceil(projectarray.length / 3);

        for (i=0; i<3; i++)
        {
            temparray = projectarray.slice(i * chunk_size, i * chunk_size + chunk_size);
            var box = '<div class="col-md-4" >';
            $.each(temparray, function(k, v) {
                box += '<div class="panel panel-default panel-project" id="project-panel-' +
                          v.key + '">' +
                          '<div class="panel-body">' +
                          '<div class="row-fluid row-flex" id="project-panel-row">' +
                          '<div class="col-md-2 project-panel-logo">';

                if (v.value.logo) {
                    box += '<img src="data:image/png;base64,' + v.value.logo + '">';
                } else {
                    box += '<img src="https://www.gravatar.com/avatar/?s=50">';
                }

                box +=    '</div> '+
                          '<div class="col-md-9 project-panel-name">' +
                          '<h2><a href="project.html?pid=' + v.key + '"><b>' + v.key + '</b></a></h2></div>' +
                          '<div class="col-md-1">' +
                          '<a id="toggle-button-' + v.key + '" class="btn btn-default">' +
                          '<i class="glyphicon glyphicon-menu-down project-panel-button" aria-hidden="true"></i></a></div>';

                var middle = '<div class="col-md-12 project-panel-detail" id="project-panel-detail">' +
                             '<div class="blank-separator"></div>';

                if (v.value.description) {
                    middle += '<h3>' + v.value.description + '</h3>';
                    middle += '<div class="blank-separator"></div>';
                }
                middle += '<table class="table">';
                middle += '<tr>';
                middle += '<th>Repository</th>';
                middle += '<th>Branches</th>';
                middle += '</tr>';

                var repos = {};
                $.each(v.value['repos'], function(key, repo) {
                    if (!(repo.name in repos)) {
                        repos[repo.name] = [];
                        repos[repo.name].push(repo.branch);
                    } else {
                        repos[repo.name].push(repo.branch);
                    }
                });
                repo_keys = Object.keys(repos);
                repo_keys.sort();

                var line ='<tr>';
                $.each(repo_keys, function(rid, rname) {
                    line += '<td><a href="project.html?pid=' + v.key;
                    line += '&inc_repos=';
                    branches = repos[rname];
                    $.each(branches, function(i, bname) {
                        var sep = ',';
                        if (i === 0) {
                            sep = '';
                        }
                        line += sep + rname + ':' + bname;
                    });
                    line += '">' + rname + '</a></td>';
                    line += '<td>';
                    $.each(branches, function(i, bname) {
                        line += '<span><a href="project.html?pid=' + v.key + '&inc_repos=' + rname + ':' + bname + '">' + bname +'</a></span> ';
                    });
                    line += '</td>';
                    line += '</tr>';
                });

                middle += line;
                middle += '</table></div></div></div></div>';

                box += middle;
            });
            box += '</div>';
            $("#project-results").append(box);
        }
    }

    $.getJSON("api/v1/projects/projects")
        .done(
            function(data) {
                fill_result(data);
            })
        .fail(
            function(err) {
                console.log(err);
            });

    $(document).on('click',"a[id^=toggle-button-]",function(){
        $(this).find('i').toggleClass('glyphicon-menu-down').toggleClass('glyphicon-menu-up');
        $(this).parent().parent().find('#project-panel-detail').toggle();
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
            ret = create_alpha_index(data);
            index = ret[0];
            sindex = ret[1];
            $("#groups-index").empty();
            $.each(sindex, function(i, v) {
                p = v.toUpperCase();
                $("#groups-index").append(
                    "<span id='groups-index'><a href='groups.html?prefix=" + v + "'><b>" + p + " </b></a></span>");
            });
        })
        .fail(function(err) {
            console.log(err);
        });
    $("#groups-table-progress").append(
        '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
    var gg_d = get_groups(false, prefix);
    gg_d
        .done(
            function(data) {
                $("#groups-table-progress").empty();
                $("#groups-table").empty();
                $("#groups-table").append("<table class=\"table table-striped\">");
                var theader = "<tr>";
                theader += "<th>Group name</th>";
                theader += "<th>Group domains</th>";
                theader += "<th>Group description</th>";
                theader += "<th>Group members</th>";
                $("#groups-table table").append(theader);
                groups = [];
                $.each(data, function(gid, gdata) {
                    groups.push(gid);
                });
                groups.sort();
                $.each(groups, function(i, gid) {
                    var elm = "<tr>";
                    elm += "<td><a href=group.html?gid=" + encodeURIComponent(gid) + ">" + gid + "</a></td>";
                    elm += "<td>" + data[gid]['domains'] + "</td>";
                    elm += "<td>" + data[gid]['description'] + "</td>";
                    elm += "<td>";
                    $.each(data[gid]['members'], function(cid, cdata) {
                        elm += "<span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                            cdata['gravatar'] + "?s=20'></span><span style='padding-right: 5px'>" +
                            "<a href=contributor.html?cid=" + cid + ">" + cdata['name'] + "</a></span>";
                    });
                    elm += "</td>";
                    $("#groups-table table").append(elm);
                });
                $("#groups-table").append("</table>");
            })
        .fail(
            function(err) {
                $("#groups-table-progress").empty();
                console.log(err);
            });
}

function contributor_page_init() {
    install_date_pickers();

    cid = getUrlParameter('cid');
    pid = getUrlParameter('pid');

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }
    var inc_repos_detail = false;
    if (getUrlParameter('inc_repos_detail') == 'on') {
        inc_repos_detail = true;
        $('#inc_repos_detail').prop('checked', true);
    }

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

    $.getJSON("api/v1/projects/projects")
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
                names = [];
                $.each(data['projects'], function(i, o) {
                    names.push(i);
                });
                names.sort();
                $.each(names, function(i, v) {
                    $('#projects-filter').append($('<option>', {
                        text: v,
                        value: v
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

        $.getJSON("api/v1/projects/projects")
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
    $("#selectrelease").click(function(){
        var rdate = $('#releases').val();
        if (pickupdatetarget === 'fromdatepicker') {$( "#fromdatepicker" ).datepicker('setDate', rdate);}
        if (pickupdatetarget === 'todatepicker')  {$( "#todatepicker" ).datepicker('setDate', rdate);}
    });

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    });

    d = get_infos(pid, undefined, cid, undefined);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];
        if(idata.commits_amount > 0) {
            install_paginator(pid, undefined, cid, undefined, idata.commits_amount, true);
            get_commits(pid, undefined, cid, undefined, undefined, true);

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, undefined, cid, undefined, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the top project by commits
            $("#topprojects-bycommits-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_projects_commit_deferred = get_top(
                pid, undefined, cid, undefined, 'projects', 'bycommits');
            top_projects_commit_deferred
                .done(function(top) {
                    $("#topprojects-bycommits-progress").empty();
                    top_t = build_top_projects_table(
                        top, inc_repos_detail);
                    $("#topprojects").append(top_t);
                })
                .fail(function(err) {
                    $("#topprojects-bycommits-progress").empty();
                    $("#topprojects").empty();
                    console.log(err);
                });

            // Fill the top project by lines changed
            $("#topprojects-bylchanged-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_projects_lchanged_deferred = get_top(
                pid, undefined, cid, undefined, 'projects', 'bylchanged');
            top_projects_lchanged_deferred
                .done(function(top) {
                    $("#topprojects-bylchanged-progress").empty();
                    top_t = build_top_projects_table(
                        top, inc_repos_detail);
                    $("#topprojects_m").append(top_t);
                })
                .fail(function(err) {
                    $("#topprojects-bylchanged-progress").empty();
                    $("#topprojects_m").empty();
                    console.log(err);
                });
        } else {
            $("#empty-warning").show();
            $("#infos-duration").hide();
            $("#infos-first_commit").hide();
            $("#infos-last_commit").hide();
            $("#infos-projects_amount").hide();
            $("#infos-repos_amount").hide();
            $("#commits_histo_div").hide();
            $("#top_projects_c_div").hide();
            $("#top_projects_lc_div").hide();
            $("#commits_listing_div").hide();
        }
    });
}

function group_page_init(commits_amount) {

    install_date_pickers();

    gid = getUrlParameter('gid');
    pid = getUrlParameter('pid');

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }

    var inc_repos_detail = false;
    if (getUrlParameter('inc_repos_detail') == 'on') {
        inc_repos_detail = true;
        $('#inc_repos_detail').prop('checked', true);
    }

    $.getJSON("api/v1/projects/projects")
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
                names = [];
                $.each(data['projects'], function(i, o) {
                    names.push(i);
                });
                names.sort();
                $.each(names, function(i, v) {
                    $('#projects-filter').append($('<option>', {
                        text: v,
                        value: v
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

        $.getJSON("api/v1/projects/projects")
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

    $('#projects').on('change', function() {
        $('#releases')
            .find('option')
            .remove()
            .end();
        if (this.value === '') {return 1;}
        get_releases(this.value);
    });

    d = get_infos(pid, undefined, undefined, gid);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];

        if(idata.commits_amount > 0) {
            install_paginator(pid, undefined, undefined, gid, idata.commits_amount, true);
            get_commits(pid, undefined, undefined, gid, undefined, true);

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, undefined, undefined, gid, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the histo author selector
            $("#history-author-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var cont_h_deferred = get_histo(pid, undefined, undefined, gid, 'authors');
            cont_h_deferred
                .done(function(data) {
                    $("#history-author-progress").empty();
                    gen_histo(data, 'history_author');
                })
                .fail(function(err) {
                    $("#history-author-progress").empty();
                    console.log(err);
                });

            // Fill the top project by commits
            $("#topprojects-bycommits-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_projects_commit_deferred = get_top(
                pid, undefined, undefined, gid, 'projects', 'bycommits');
            top_projects_commit_deferred
                .done(function(top) {
                    $("#topprojects-bycommits-progress").empty();
                    top_t = build_top_projects_table(
                        top, inc_repos_detail);
                    $("#topprojects").append(top_t);
                })
                .fail(function(err) {
                    $("#topprojects-bycommits-progress").empty();
                    $("#topprojects").empty();
                    console.log(err);
                });

            // Fill the top project by lines changed
            $("#topprojects-bylchanged-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_projects_lchanged_deferred = get_top(
                pid, undefined, undefined, gid, 'projects', 'bylchanged');
            top_projects_lchanged_deferred
                .done(function(top) {
                    $("#topprojects-bylchanged-progress").empty();
                    top_t = build_top_projects_table(
                        top, inc_repos_detail);
                    $("#topprojects_m").append(top_t);
                })
                .fail(function(err) {
                    $("#topprojects-bylchanged-progress").empty();
                    $("#topprojects_m").empty();
                    console.log(err);
                });

            // Fill the top authors by commits
            $("#topauthor-bycommits-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_auth_commit_deferred = get_top(
                pid, undefined, undefined, gid, 'authors', 'bycommits');
            top_auth_commit_deferred
                .done(function(top) {
                    $("#topauthor-bycommits-progress").empty();
                    top_h = build_top_authors_head(top, 'commits');
                    $("#topauthors_gravatar").append(top_h);
                    top_b = build_top_authors_body(top);
                    $("#topauthors").append(top_b);
                })
                .fail(function(err) {
                    $("#topauthor-bycommits-progress").empty();
                    $("#topauthors_gravatar").empty();
                    $("#topauthors").empty();
                    console.log(err);
                });

            // Fill the top authors by line changes
            $("#topauthor-bylchanged-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_auth_lchanged_deferred = get_top(
                pid, undefined, undefined, gid, 'authors', 'bylchanged');
            top_auth_lchanged_deferred
                .done(function(top) {
                    $("#topauthor-bylchanged-progress").empty();
                    top_h = build_top_authors_head(top, 'lines changed');
                    $("#topauthors_m_gravatar").append(top_h);
                    top_b = build_top_authors_body(top);
                    $("#topauthors_m").append(top_b);
                })
                .fail(function(err) {
                    $("#topauthor-bylchanged-progress").empty();
                    $("#topauthors_m_gravatar").empty();
                    $("#topauthors_m").empty();
                    console.log(err);
                });
        } else {
            $("#empty-warning").show();
            $("#commits_histo_div").hide();
            $("#contributors_histo_div").hide();
            $("#top_projects_c_div").hide();
            $("#top_projects_lc_div").hide();
            $("#top_authors_c_div").hide();
            $("#top_authors_lc_div").hide();
            $("#commits_listing_div").hide();
        }
    });
}

function project_page_init() {
    install_date_pickers();

    var selected_metadata = [];

    pid = getUrlParameter('pid');
    tid = getUrlParameter('tid');

    if (getUrlParameter('inc_merge_commit') == 'on') {
        $('#inc_merge_commit').prop('checked', true);
    }


    if (getUrlParameter('metadata')) {
        selected_metadata = getUrlParameter('metadata').split(',');
        $.each(selected_metadata, function(i, v) {
            $("#metadata-selected").append('<span class="badge">'+v+'</div>');
        });
    }

    var newlocation;

    $("#filter").click(function(){
        if (pid) {
            newlocation = "project.html?pid=" + pid;
        }
        else {
            newlocation = "project.html?tid=" + tid;
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
        if ($('#groups').val() != "") {
            newlocation = newlocation + "&exc_groups=" + encodeURIComponent($('#groups').val());
        }
        if (selected_metadata.length > 0) {
            newlocation = newlocation + "&metadata=" + encodeURIComponent(selected_metadata.toString());
        }
        window.location = newlocation;
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

    // Fill the groups selector
    var defer = get_groups(true);
    defer.done(
        function(data) {
            $('#groups')
                .find('option')
                .remove()
                .end();
            $('#groups').append($('<option>', {
                text: 'Select a group',
                value: ''
            }));
            groups = [];
            $.each(data, function(k, v) {
                groups.push(k);
            });
            groups.sort();
            $.each(groups, function(i, k) {
                $('#groups').append($('<option>', {
                    text: k,
                    value: k
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

    // Get the info and continue to fill the page if commits_amount is > 0
    d = get_infos(pid, tid, undefined, undefined);
    d.done(function(rdata, idata, cdata, gdata) {
        idata = idata[0];
        rdata = rdata[0];
        if (idata.commits_amount > 0) {
            install_paginator(
                pid, tid, undefined,
                undefined, idata.commits_amount, true);

            get_metadata_keys(pid, tid, undefined);

            get_commits(
                pid, tid, undefined, undefined,
                undefined, true);

            get_releases(pid, tid);

            // Fill project refs selector
            refs = [];
            $.each(rdata, function(i, v) {
                val = v.name + ':' + v.branch;
                refs.push(val);
            });
            refs.sort();
            $.each(refs, function(i, ref) {
                $('#repositories').append($('<option>', {
                    text: ref,
                    value: ref
                }));
            });
            // Select the ones specified in the url
            if (getUrlParameter('inc_repos')) {
                selected = getUrlParameter('inc_repos').split(',');
                $('#repositories').val(selected);
            }

            // Fill the histo commits selector
            $("#history-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var c_h_deferred = get_histo(pid, tid, undefined, undefined, 'commits');
            c_h_deferred
                .done(function(data) {
                    $("#history-progress").empty();
                    gen_histo(data, 'history');
                })
                .fail(function(err) {
                    $("#history-progress").empty();
                    console.log(err);
                });

            // Fill the histo author selector
            $("#history-author-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var cont_h_deferred = get_histo(pid, tid, undefined, undefined, 'authors');
            cont_h_deferred
                .done(function(data) {
                    $("#history-author-progress").empty();
                    gen_histo(data, 'history_author');
                })
                .fail(function(err) {
                    $("#history-author-progress").empty();
                    console.log(err);
                });

            // Fill the top authors by commits
            $("#topauthor-bycommits-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_auth_commit_deferred = get_top(
                pid, tid, undefined, undefined, 'authors', 'bycommits');
            top_auth_commit_deferred
                .done(function(top) {
                    $("#topauthor-bycommits-progress").empty();
                    top_h = build_top_authors_head(top, 'commits');
                    $("#topauthors_gravatar").append(top_h);
                    top_b = build_top_authors_body(top);
                    $("#topauthors").append(top_b);
                })
                .fail(function(err) {
                    $("#topauthor-bycommits-progress").empty();
                    $("#topauthors_gravatar").empty();
                    $("#topauthors").empty();
                    console.log(err);
                });

            // Fill the top authors by line changes
            $("#topauthor-bylchanged-progress").append(
                '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
            var top_auth_lchanged_deferred = get_top(
                pid, tid, undefined, undefined, 'authors', 'bylchanged');
            top_auth_lchanged_deferred
                .done(function(top) {
                    $("#topauthor-bylchanged-progress").empty();
                    top_h = build_top_authors_head(top, 'lines changed');
                    $("#topauthors_m_gravatar").append(top_h);
                    top_b = build_top_authors_body(top);
                    $("#topauthors_m").append(top_b);
                })
                .fail(function(err) {
                    $("#topauthor-bylchanged-progress").empty();
                    $("#topauthors_m_gravatar").empty();
                    $("#topauthors_m").empty();
                    console.log(err);
                });
        } else {
            $("#empty-warning").show();
            $("#infos-duration").hide();
            $("#infos-first_commit").hide();
            $("#infos-last_commit").hide();
            $("#top_authors_c_div").hide();
            $("#infos-authors_amount").hide();
            $("#commits_histo_div").hide();
            $("#contributors_histo_div").hide();
            $("#top_authors_c_div").hide();
            $("#top_authors_lc_div").hide();
            $("#commits_listing_div").hide();
        }
    });
}

function contributors_page_init() {

    function fill_resultinfos_gen(leaf) {
        $("#resultinfos").empty();
        $("#resultinfos").append(leaf);
    }
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
                v.gravatar + '?s=20"></span>' +
                '<span><a href=contributor.html?cid=' +
                k + '>' + v.name + '</a></span></h3>' +
                '</div></div></div>';
            $("#search-results").append(box);
        });
    }
    $('#search-txt').bind("enterKey",function(e){
        var args = {};
        args['query'] = $("#search-txt").val();
        fill_resultinfos_gen('<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
        $.getJSON("api/v1/search/search_authors", args)
            .done(
                function(data) {
                    fill_resultinfos(data);
                    fill_result(data);
                })
            .fail(
                function(err) {
                    fill_resultinfos_gen('Server side error');
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
    $.getJSON("api/v1/tags/tags", args)
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
        $.getJSON("api/v1/metadata/metadata", args)
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

    $.getJSON("api/v1/metadata/metadata", args)
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

function get_commits(pid, tid, cid, gid, page, with_projects_c) {
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

    $("#commits-table-progress").append(
        '&nbsp;<span class="glyphicon glyphicon-refresh glyphicon-refresh-animate"></span>');
    $.getJSON("api/v1/commits/commits", args).done(function(data) {
        $("#commits-table").empty();
        $("#commits-table-progress").empty();
        $("#commits-table").append("<table class=\"table table-striped\">");
        var theader = "<tr>";
        theader += "<th>Date of commit</th>";
        if (with_projects_c) {
            theader += "<th>Projects</th>";
        }
        theader += "<th>Repository refs</th>";
        theader += "<th>Author/Committer</th>";
        theader += "<th>Message</th>";
        theader += "<th>Changed lines</th>";
        theader += "<th>Time To Land</th>";
        theader += "</tr>";
        $("#commits-table table").append(theader);
        $.each( data[2], function(k, v) {
            var cmt_date = new Date(1000 * v['committer_date']);
            cmt_date = moment(cmt_date);
            var elm = "<tr>";
            if (with_projects_c) {
                var projects = "";
                $.each(v['projects'], function(i, p) {
                    if (i > 0) {projects += "<br>";}
                    projects += p;
                });
            }
            var refs = "";
            $.each(v['repos'], function(i, p) {
                if (i > 0) {refs += "<br>";}
                refs += p;
            });
            elm += "<td>" + cmt_date.format("MMM D, YYYY") + "</td>";
            if (with_projects_c) {
                elm += "<td>" + projects + "</td>";
            }
            elm += "<td>" + refs + "</td>";
            elm += "<td><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                v['author_gravatar'] + "?s=20'></span><span><a href=contributor.html?cid=" +
                v['cid'] + ">" + v['author_name'] + "</a></span>";
            if (v['ccid'] != v['cid']) {
                elm += "<br><span style='padding-right: 5px'><img src='https://www.gravatar.com/avatar/" +
                    v['committer_gravatar'] + "?s=20'></span><span><a href=contributor.html?cid=" +
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
            $("#commits-table-progress").empty();
            console.log(err);
        });
}

function check_fragment() {
    var hash = window.location.hash || "#page-1";
    hash = hash.match(/^#page-(\d+)$/);
    if(hash) {
        page = parseInt(hash[1]);
        $("#pagination").pagination('selectPage', page);
    }
}

function install_paginator(pid, tid, cid, gid, items_amount, with_projects_c) {
    if (items_amount >= 1000) {
        // Limit the amount of pages to 100
        // User should use the calendar filter to dig in the results
        items_amount = 1000;
    }
    $(window).bind("popstate", check_fragment);
    $('#pagination').pagination({
        items: items_amount,
        itemsOnPage: 10,
        cssStyle: 'light-theme',
        onPageClick: function(pageNumber, ev) {
            // The paginator will update the page hash fragment
            // To avoid the double get_commits call (due to the bind of the popstate event)
            // I skip calling get_commit if ev is defined.
            // On hash change/history update the paginator is refresh
            // On click on a button the paginator is refresh
            if (!(ev)) {
                get_commits(pid, tid, cid, gid, (pageNumber - 1) * 10);
            }
        }
    });
}
