var app = angular.module('app', ['ui.router', 'ui.bootstrap']);

app.factory('API', function($http) {
    return {
        get: function(name, params) {
            return $http.get('/api/'+ name +'/', {params: params});
        },
        post: function(name, data) {
            return $http.post('/api/'+ name +'/', data);
        },
        put: function(name, data) {
            return $http.put('/api/'+ name +'/', data);
        },
        patch: function(name, data) {
            return $http.patch('/api/'+ name +'/', data);
        }
    };
});

app.config(function($stateProvider, $urlRouterProvider, $httpProvider) {
    $urlRouterProvider.otherwise("/");

    $stateProvider
        .state('index', {
            url: "/?page&search",
            templateUrl: "/static/templates/test_execution_list.html",
            controller: 'TestExecutionList'
        })
        .state('login', {
            url: "/login/",
            templateUrl: "/static/templates/login.html",
            controller: 'Login'
        })
        .state('logout', {
            url: "/logout/",
            controller: 'Logout'
        })
        .state('detail', {
            url: "/execution/:id/",
            templateUrl: "/static/templates/test_execution_detail.html",
            controller: 'TestExecutionDetail'
        })
        .state('testjob-list', {
            url: "/testjob/?page&search",
            templateUrl: "/static/templates/test_job_list.html",
            controller: 'TestJobList'
        })
        .state('testjob-detail', {
            url: "/testjob/:id",
            templateUrl: "/static/templates/test_job.html",
            controller: 'TestJob'
        })
        .state('testjob-detail.view', {
            url: "/view/",
            templateUrl: "/static/templates/test_job_view.html"
        })
        .state('testjob-detail.edit', {
            url: "/edit/",
            templateUrl: "/static/templates/test_job_edit.html",
            controller: 'TestJobEdit'
        })
        .state('testplan-list', {
            url: "/testplan/",
            templateUrl: "/static/templates/test_plan_list.html",
            controller: 'TestPlanList'
        })
        .state('testplan-detail', {
            url: "/testplan/:id/",
            templateUrl: "/static/templates/test_plan_detail.html",
            controller: 'TestPlanDetail'
        })
        .state('testplan-new', {
            url: "/testplan/new",
            controller: 'TestPlanNew',
            templateUrl: "/static/templates/test_plan_detail.html"
        })
        .state('404', {
            url: "/404",
            templateUrl: "/static/templates/404.html"
        });

    $httpProvider.defaults.headers.common['Pragma'] = 'no-cache';
    $httpProvider.interceptors.push(function($q, $injector) {
        return {
            request: function(config) {
                token = localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = "Token " + token;
                }
                return config;
            },
            responseError: function(response) {
                if (response.status === 401 && response.config.url !== "/api/user/") {
                    $injector.get('$state').go('login', {}, {location: 'replace'});
                }
                if (response.status === 404) {
                    $injector.get('$state').go('404', {}, {location: 'replace'});
                }
                return $q.reject(response);
            }
        };
    });

});

app.run(function ($rootScope, API) {
    API.get('user').success(function(user) {
        $rootScope.user = user;
        $rootScope.ready = true;
    }).error(function() {
        $rootScope.ready = true;
    });
});

app.controller('Login', function($state, $scope, API, $rootScope) {
    $scope.submit = function() {

        API.post('login', $scope.credentials)
            .success(function(response) {

                localStorage.setItem('token', response.token);

                API.get('user').success(function(user) {
                    $rootScope.user = user;
                });
                $state.go('index');
            })
            .error(function(errors) {
                $scope.errors = errors;
            });
    };
});

app.controller('Logout', function($rootScope, $state) {
    localStorage.removeItem("token");
    $rootScope.user = null;
    $state.go('index');
});


app.controller('TestJob', function($state, $stateParams, $scope, API, $q) {
    API.get("test-job/" + $stateParams.id).then(function(response) {
        $scope.data = response.data;
        $scope.loaded = true;

        if ($scope.data.kind === "manual" && $scope.user) {
            $state.go('testjob-detail.edit', {}, {location: "replace"});
        } else {
            $state.go('testjob-detail.view', {}, {location: "replace"});
        }

    });

    $scope.$watch('data.results', function(tests, b) {
        if (!tests) return;
        var total = _.keys(tests).length;
        var statuses = _.countBy(tests, 'status');

        $scope.progress = {
            "pass": {'width': (statuses.pass / total * 100) + '%' },
            "skip": {'width': (statuses.skip / total * 100) + '%' },
            "fail": {'width': (statuses.fail / total * 100) + '%' },
            "idle": {'width': (statuses.null / total * 100) + '%' }
        };
    }, true);

    $scope.saveNotes = function() {
        API.patch("test-job/" + $stateParams.id, {notes: $scope.data.notes});
    };

});

app.controller('TestJobEdit', function($state, $stateParams, $scope, API, $q) {

    $scope.issueSources = API.get('issue-kind').success(function(data) {
        $scope.issueSources = data;
    });

    $scope.selectIssueKind = function(source) {
        $scope.selected = source;
    };

    $scope.cssStatusClass = function(test) {
        if (test.status == 'pass')
            return 'panel-success';
        if (test.status == 'skip')
            return 'panel-warning';
        if (test.status == 'fail')
            return 'panel-danger';
        return '';
    };

    $scope.forceSetStatus = function(test, status) {
        var data = {
            status: test.status === status ? null : status
        };

        API.put("test-result/" + $state.params.id + '/' + test.name, data)
            .success(function(data) {
                angular.copy(data, test);
            });
    };


    $scope.setStatus = function(test, status) {
        var data = {
            status: test.status === status ? null : status,
            modified_at: test.modified_at
        };

        API.put("test-result/" + $state.params.id + '/' + test.name, data)
            .success(function(data) {
                angular.copy(data, test);
            })
            .error(function(data) {
                test.conflict = data;
            });
    };
});

app.controller('TestPlanNew', function($state, $scope, API, $q) {

    API.get('test-manual').then(function(response) {
        $scope.available = response.data;
        $scope.loaded = true;
    });

    $scope.definition = {
        'name': '',
        'data': {'tests': []},
        'kind': 'manual'
    };

    $scope.selectTest = function(name) {
        $scope.available.tests[name].active ^= true;

        if ($scope.available.tests[name].active) {
            $scope.definition.data.tests.push(name);
        } else {
            _.pull($scope.definition.data.tests, name);
        }
    };

    $scope.submit = function() {

        API.post('definition', $scope.definition)
            .error(function(errors) {
                $scope.errors = errors;
            })
            .success(function(response) {
                $state.go("testplan-list");
            });
    };
});

app.controller('TestPlanDetail', function($state, $scope, API, $q) {

    $q.all([
        API.get('test-manual'),
        API.get('definition/' + $state.params.id)]).then(function(responses) {

            $scope.available = responses[0].data;
            $scope.definition = responses[1].data;

            _.each($scope.definition.data.tests, function(name) {
                $scope.available.tests[name].active = true;
            });
            $scope.loaded = true;
        });

    $scope.selectTest = function(name) {
        $scope.available.tests[name].active ^= true;

        if ($scope.available.tests[name].active) {
            $scope.definition.data.tests.push(name);
        } else {
            _.pull($scope.definition.data.tests, name);
        }
    };

    $scope.submit = function() {
        API.put('definition/' + $state.params.id, $scope.definition)
            .error(function(errors) {
                $scope.errors = errors;
            })
            .success(function(response) {
                $state.go("testplan-list");
            });
    };

});


app.controller('TestPlanList', function($state, $stateParams, $scope, API) {
    API.get('definition').then(function(response) {
        $scope.page = response.data;
        $scope.loaded = true;
    });
});


app.controller('TestJobList', function($state, $stateParams, $scope, API) {

    $scope.search = $stateParams.search;

    $scope.makeSearch = function() {
        $stateParams.search = $scope.search;
        $stateParams.page = 1;
        $state.go($state.current, $stateParams, {notify: false});

        API.get('test-job', $stateParams).then(function(response) {
            $scope.page = response.data;
        });
    };

    API.get('test-job', $stateParams).then(function(response) {
        $scope.page = response.data;
        $scope.loaded = true;
    });
});

app.controller('TestExecutionList', function($state, $stateParams, $scope, API, $rootScope) {

    $scope.search = $stateParams.search;

    $scope.makeSearch = function() {
        $stateParams.search = $scope.search;
        $stateParams.page = 1;
        $state.go($state.current, $stateParams, {notify: false});

        API.get('test-execution', $stateParams).then(function(response) {
            $scope.page = response.data;
        });
    };

    API.get('test-execution', $stateParams).then(function(response) {
        $scope.page = response.data;
        $scope.loaded = true;
    });

});

app.controller('TestExecutionDetail', function($state, $stateParams, $scope, API) {

    API.get('test-execution/' + $stateParams.id)
        .then(function(response) {
            $scope.item = response.data;
            $scope.loaded = true;
        });

    API.get('definition', {no_pagination:true})
        .then(function(response) {
            $scope.definitions = response.data;
        });

    API.get('test-job', {test_execution:$stateParams.id, no_pagination:true})
        .then(function(response) {
            $scope.testjobs = response.data;
        });

    $scope.addTestJobManual = function() {
        var data = {
            "test_execution": $stateParams.id,
            "definition": $scope.definitionSelected
        };
        API.post('test-job', data).then(function() {
            API.get('test-job', {test_execution:$stateParams.id, no_pagination:true})
                .then(function(response) {
                    $scope.testjobs = response.data;
                });
        });
    };
});

app.directive('pagination', function($state, $httpParamSerializer, $location) {
    return {
        restrict: 'E',
        scope: {
            page: '='
        },
        templateUrl: '/static/templates/_pagination.html',
        link: function(scope, elem, attrs) {

            scope.goNext = function() {
                scope.loaded = false;
                $state.params.page = scope.page.page.next;
                $state.go($state.current, $state.params, {reload: true});
            };

            scope.goBack = function() {
                scope.loaded = false;
                $state.params.page = scope.page.page.previous;
                $state.go($state.current, $state.params, {reload: true});
            };
        }
    };
});

app.directive('progress', function($state, $httpParamSerializer, $location) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            results: '='
        },
        templateUrl: '/static/templates/_progress.html',
        link: function(scope, elem, attrs) {

            scope.$watch('results', function(tests, b) {
                if (!tests) return;
                var total = _.keys(tests).length;
                var statuses = _.countBy(tests, 'status');

                scope.progress = {
                    "pass": {'width': (statuses.pass / total * 100) + '%' },
                    "skip": {'width': (statuses.skip / total * 100) + '%' },
                    "fail": {'width': (statuses.fail / total * 100) + '%' },
                    "idle": {'width': (statuses.null / total * 100) + '%' }
                };
            }, true);

        }
    };
});


app.filter('join', function() {
    return function(input) {
        return (input instanceof Array) ? input.join(", "): input;
    };
});
