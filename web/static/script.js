$(function(){
    var loading = '<li class="list-group-item disabled text-center">... loading ...</li>',
        error = '<li class="list-group-item list-group-item-danger">###</li>',
        filter = '';

    /**
     * Dashboard instance-recipe handlers
     */
    function get_opposing_model(model) {
        return model == 'recipe' ? 'instance' : 'recipe';
    }
    function refresh(model, only_with_connections, callback) {
        $('#' + model + 's').html(loading);
        $.getJSON('/json/' + model + 's' +
            ($.isArray(only_with_connections) ? ('/' + only_with_connections.join('-')) : ''),
            (function(callback){ return function (_data) {

            if (_data['status'] == 200) {
                $('#' + model + 's').html('');
                var opposing_model = get_opposing_model(model);
                $.each(_data['data'], function (i, elem) {
                    var opposing_model_from_latest_run = elem.latest_run[opposing_model];
                    $('#' + model + 's').append(
                        '<li class="list-group-item px-1' + (typeof(elem.active) != 'undefined' && !elem.active ?
                        ' list-group-item-light" title="currently inactive"' : '"') + '>' +
                        '<div class="d-flex flex-row">' +
                        '<div class="pr-2">' +
                        '<input type="checkbox" data-uid="' + elem.uid + '">' +
                        '</div>' +
                        '<div class="">' +
                        '<a href="/' + model + '/' + elem.uid + '" class="d-block' +
                        (typeof(elem.active) != 'undefined' && !elem.active ? ' text-muted' : '') + '">' +
                        elem.name +
                        '</a>' +
                        (elem.description ? (
                            '<p class="mb-1">' +
                            elem.description.replace(/\r\n|\r|\n/g, '<br />') +
                            '</p>'
                        ) : '') +
                        (elem.latest_run ? (
                            '<small class="text-muted">Last run was <a href="/' + opposing_model + '/' +
                            opposing_model_from_latest_run.uid + '">' +
                            opposing_model_from_latest_run.name.substr(0, 12) +
                            (opposing_model_from_latest_run.name.length > 12 ? '...' : '') +
                            '</a> on <a href="/json/run/' + elem.latest_run.uid + '">' +
                            elem.latest_run.created + '</a></small>'
                        ) : '') +
                        '</div>' +
                        '</div>' +
                        '</li>');
                });
                update_status(model);
                init_run_detail_view_handler();
                init_instance_recipe_connector(model);
                if(typeof(callback) == 'function') {
                    callback();
                }
            } else {
                $('#' + model + 's').html(error.replace('###', _data['message']));
            }
        }})(callback));
    }
    function init_instance_recipe_connector(model) {
        $('#' + model + 's input[type="checkbox"][data-uid]').off('change').on('change', function() {
            if($(this).is(':checked')) {
                $(this).parents('li.list-group-item').addClass('list-group-item-secondary');
            } else {
                $(this).parents('li.list-group-item').removeClass('list-group-item-secondary');
            }
            var opposing_model = get_opposing_model(model),
                selected_opposing_models = $('#' + opposing_model + 's input[type="checkbox"][data-uid]:checked'),
                selected_opposing_model = selected_opposing_models.length,
                selected_models = $('#' + model + 's input[type="checkbox"][data-uid]:checked');
            if(selected_opposing_model == 0) {
                if(selected_models.length == 0) {
                    refresh(opposing_model);
                    filter = '';
                } else {
                    refresh(opposing_model, $.map(selected_models, function(o) {return $(o).data('uid')}));
                    filter = model;
                }
            } else {
                if(filter == model) {
                    var selected = $.map(selected_opposing_models, function(o) {return $(o).data('uid')});
                    if(selected_models.length == 0) {
                        refresh(opposing_model, null, (function(_model, _selected) {
                            return function() {
                                $.each(_selected, function(i, _uid) {
                                console.log('#' + _model + 's input[type="checkbox"][data-uid="' + _uid + '"]');
                                    $('#' + _model + 's input[type="checkbox"][data-uid="' + _uid + '"]').click()
                                });
                        }})(opposing_model, selected));
                    } else {
                        refresh(opposing_model, $.map(selected_models, function(o) {return $(o).data('uid')}),
                            (function(_model, _selected) { return function() {
                                $.each(_selected, function(i, _uid) {
                                console.log('#' + _model + 's input[type="checkbox"][data-uid="' + _uid + '"]');
                                    $('#' + _model + 's input[type="checkbox"][data-uid="' + _uid + '"]').click()
                                });
                        }})(opposing_model, selected));
                    }
                } else {
                    update_status(model);
                }
            }
        });
    }
    function update_status(model) {
        var selected_models = $('#' + model + 's input[type="checkbox"][data-uid]:checked'),
            selected_model = selected_models.length,
            opposing_model = get_opposing_model(model),
            selected_opposing_models = $('#' + opposing_model + 's input[type="checkbox"][data-uid]:checked'),
            selected_opposing_model = selected_opposing_models.length;
        if(selected_opposing_model > 0) {
            if(selected_model > 0) {
                $('#' + model + '_status').html(
                    selected_model + ' ' + model + '(s) selected based on ' +
                    selected_opposing_model + ' ' + opposing_model + '(s). ' +
                    '<a href="#" data-selectall="' + model + '">Select all</a>'
                );
            } else {
                $('#' + model + '_status').html(
                    'Filtered based on ' + selected_opposing_model + ' ' + opposing_model + '(s). ' +
                    '<a href="#" data-selectall="' + model + '">Select all</a>'
                );
            }
            $('#' + model + '_status a[data-selectall]').off('click').on('click', function(event) {
                event.preventDefault();
                $('#' + $(this).data('selectall') + 's input[type="checkbox"][data-uid]:not(:checked)').click();
            });
        } else {
            if(selected_model > 0) {
                $('#' + model + '_status').text(
                    selected_model + ' ' + model + '(s) selected, serving as filter for ' + opposing_model + 's'
                );
            } else {
                $('#' + model + '_status').text('Showing all ' + model + 's');
            }
        }
        if(selected_model > 0 && selected_opposing_model > 0) {
            $('#' + model + '_count').text(selected_model);
            $('#' + opposing_model + '_count').text(selected_opposing_model);
            var str_model = $.map(selected_models, function(o) {return $(o).data('uid')}).join('-'),
                str_opposing = $.map(selected_opposing_models,function(o) {return $(o).data('uid')}).join('-');
            $('#download #instance_list').val((model == 'instance' ? str_model : str_opposing));
            $('#download #recipe_list').val((model == 'instance' ? str_opposing : str_model));
            $('#download').removeClass('d-none');
        } else {
            $('#download').addClass('d-none');
        }
        if((model == 'recipe' && selected_model > 0) || (opposing_model == 'recipe' && selected_opposing_model > 0)) {
            var checked_recipes = $('#recipes input[type="checkbox"][data-uid]:checked'),
                checked_recipe_str = $.map(checked_recipes, function(o) {return $(o).data('uid')}).join('-');
            $('#recipe_action').parent().find('a:not(.deactivate)')
                .attr('href', '/recipes/multiple/' + checked_recipe_str);
            $('#recipe_action').parent().find('a.deactivate')
                .attr('href', '/recipes/multiple/' + checked_recipe_str + '/1');
            $('#recipe_action').parent().removeClass('d-none');
        } else {
            $('#recipe_action').parent().addClass('d-none');
        }
    }
    refresh('instance');
    refresh('recipe');


    /**
     * Run detail-view handler
     */
    function init_run_detail_view_handler() {
        $('a[href^="/json/run/"]').off('click').on('click', function (_event) {
            _event.preventDefault();
            $.getJSON(this.href, function (_data) {
                if (_data['status'] == 200) {
                    var run = _data['run'];
                    $('#modal_run [data-column="recipe.name"]').html(run.recipe.name);
                    $('#modal_run [data-column="instance.name"]').html(run.instance.name);
                    $('#modal_run [data-column="run.runtime"]').html(run.runtime);
                    $('#modal_run .badge')
                        .removeClass('badge-success')
                        .removeClass('badge-danger')
                        .removeClass('badge-warning');
                    switch (run.status) {
                        case 'success':
                            $('#modal_run .badge')
                                .addClass('badge-success')
                                .text('Successfully terminated after ' + run.runtime + ' seconds');
                            break;
                        case 'error':
                            $('#modal_run .badge')
                                .addClass('badge-danger')
                                .text('Terminated with an error after ' + run.runtime + ' seconds');
                            break;
                        case 'config_error':
                            $('#modal_run .badge')
                                .addClass('badge-warning')
                                .text('Could not run successfully due to misconfiguration on ' + run.created);
                            break;
                        case 'command_not_found':
                            $('#modal_run .badge')
                                .addClass('badge-warning')
                                .text('Could not run successfully due to unknown commands on ' + run.created);
                            break;
                        case 'in_progress':
                            $('#modal_run .badge')
                                .addClass('badge-info')
                                .text('Currently in progress, started on ' + run.created);
                            break;
                    }
                    $('ul[data-column="log"]').html('');
                    $.each(run.log, function(i, log) {
                        $('<li class="list-group-item list-group-item-' +
                            (log.type == 'error' ? 'danger' : log.type) + '"><small class="d-block text-muted">' +
                            log.created + '</small>' + log.message + '</li>')
                            .appendTo('ul[data-column="log"]');
                    });
                    if(run.data.length == 0) {
                        $('ul[data-column="data"]').html('<li class="list-group-item"><em>no data collected</em></li>');
                    } else {
                        $('ul[data-column="data"]').html('');
                        $.each(run.data, function (i, data) {
                            $('<li class="list-group-item" data-toggle="tooltip" data-placement="left" title="Step #' +
                                data.step.sort + ' (' + data.step.type + ')">' + (
                                    data.value.length > 100 ?
                                    (data.value.substr(0, 30) + '...') :
                                    data.value
                                ) + '</li>')
                                .appendTo('ul[data-column="data"]');
                        });
                        $('[data-toggle="tooltip"]').tooltip();
                    }
                    $('#modal_run').modal('show');
                } else {
                    alert(_data['message']);
                }
            });
        });
    }
    init_run_detail_view_handler();



    /**
     * Self-updating run-view handler
     */
    function refresh_runs(ul, recipe_uid, instance_uid) {
        var runs = [];
        $(ul).html(loading);
        $.getJSON('/json/runs/' + (recipe_uid > 0 ? recipe_uid : '0') + '-' + (instance_uid > 0 ? instance_uid : '0'), function(_data) {
            if(_data['status'] == 200) {
                $(ul).html('');
                $.each(_data['data'], function(i, run) {
                    var item = $('<li class="list-group-item list-group-item-' +
                        (run.status == 'success' ? 'success' :
                            (run.status == 'in_progress' ? 'info' :
                                (run.status == 'error' ? 'danger' : 'warning'))) + '"></li>');
                    if(recipe_uid === null) {
                        item.append('<a href="/json/run/' + run.uid + '" class="d-block">' +
                            run.recipe.name + ' on ' + run.created + (run.status == 'success' ? '' : (': ' + run.status))
                            + ' (' + run.runtime + 's)</a>');
                    } else {
                        item.append('<a href="/json/run/' + run.uid + '" class="d-block">' +
                            run.created + ' on ' + run.instance.name + (run.status == 'success' ? '' : (': ' + run.status))
                            + ' (' + run.runtime + 's)</a>');
                    }
                    $(ul).append(item);
                });
                init_run_detail_view_handler();
            } else {
                $(ul).html(error.replace('###', _data['message']));
            }
        });
    }
    $('.runs[data-recipe]').each(function(i, elem) {
        refresh_runs(elem, $(elem).data('recipe'));
        setInterval(refresh_runs, 60000, elem, $(elem).data('recipe'));
    });
    $('.runs[data-instance]').each(function(i, elem) {
        refresh_runs(elem, null, $(elem).data('instance'));
        setInterval(refresh_runs, 60000, elem, null, $(elem).data('instance'));
    });


    /**
     * Instance chart initiation
     */
    $('.chart_instance').each(function(i, elem) {
        var instance = $(elem).data('instance');
        $.getJSON('/json/instance/' + instance + '/chart', function (data) {
            var letters = '0123456789ABCDEF'.split(''),
                i = 0,
                j = 0,
                color = '';
            for(i=0; i < data.datasets.length; i++) {
                color = '#';
                for(j=0; j < 3; j++) {
                    color += letters[Math.floor(16*Math.random())];
                }
                data.datasets[i]['borderColor'] = color;
            }
            new Chart(elem, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: data.datasets
                },
                options: {
                    elements: {
                        line: {
                            tension: 0,
                            fill: false
                        }
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                stepSize: 1
                            }
                        }]
                    }
                }
            });
        });
    });
});
