##############
Basic Concepts
##############

About Tasks
===========

Anything in aCrawler is a :class:`~acrawler.task.Task`, which :meth:`~acrawler.task.Task.execute` and then may yield new :class:`~acrawler.task.Task`.

There are several basic Tasks defined here.

* :class:`~acrawler.http.Request` task executes its default ``fetch()`` method to make HTTP request. Then task will automatically yield a corresponding  :class:`~acrawler.http.Response` task. You can pass a function to :attr:`~acrawler.http.Request.callback` argument and provide a :attr:`~acrawler.http.Request.family`, which are all passed to the response task.

* :class:`~acrawler.http.Response` task executes ``callback()``. It call all functions in :attr:`~acrawler.http.Response.callbacks` with http response and may yield new task. A :class:`~acrawler.http.Response` may have several callback functions (which are passed from decorator :func:`~acrawler.handlers.callback` or corresponding request's parameter).

* :class:`~acrawler.item.Item` task executes its ``custom_process()`` method, which you can rewrite.
* :class:`~acrawler.item.ParselItem` extends from :class:`~acrawler.item.Item` . It accepts a ``Selector`` and uses `Parsel <https://parsel.readthedocs.io/en/latest/>`_ to parse content.
* Any new ``Task`` yielded from an existing ``Task`` 's execution will be catched and delivered to scheduler.
* Any new ``dictionary`` yielded from an existing ``Task``'s execution will be catched as :class:`~acrawler.item.DefaultItem`.


About Families
==============

* Each :class:`~acrawler.middleware.Handler` has only one family. If a  handler's family is in a task's families, this handler matches the task and then somes fuctions will be called before and after the task.
* Each task has ``families`` (defaults to names of all base classes and itself). If you pass ``family`` to a task, it will be appended to task's families. Specially, a :class:`~acrawler.http.Request` 's user-passed ``family`` will be passed to its corresponding :class:`~acrawler.http.Response`'s family.
* ``family`` is also used for decorator :func:`~acrawler.handlers.callback` and :func:`~acrawler.middleware.register`

  * You can use decorator ``@register()`` to add a ``handler`` to crawler. It is also allowed to register a function but you should provide family, position as parameters. If a ``handler``\ 's family is in a ``task``\ 's families, then ``handler`` matches ``task``.
  * You can use decorator ``@callback(family='')`` to add a callback to response. If ``family`` in ``@callback()`` is in a response's families, then callback will be combined to this response.

