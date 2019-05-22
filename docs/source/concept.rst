##############
Basic Concepts
##############

About Tasks
===========

Anything in aCrawler is a ``Task``\ , which ``executes`` and then may yield new ``Tasks``. 

There are several basic ``Tasks`` defined here.

* ``Request`` task executes its default ``fetch()`` method and automatically  yield a corresponding  ``Response`` task. You can pass a function to its ``callback`` argument.
* ``Response`` task executes its ``callback`` function and may yield new ``Task``. A ``Response`` may have several callback functions (which are passed from request)
* ``Item`` task executes its ``custom_process`` method.
* ``ParselItem`` extends from ``Item`` . It accepts a ``Selector`` and uses ``Parsel`` to parse content.
* Any new ``Task`` yielded from an existing ``Task``\ 's execution will be catched and delivered to scheduler.
* Any new ``dictionary`` yielded from an existing ``Task``\ 's execution will be catched as ``DefaultItem``.


About Families
==============

* Each handler has only one family
* Each task has ``families`` (defaults to names of all base classes and itself). If you pass ``family`` to a task, it will be added to task's families. Specially, a ``Request``\ 's user-passed ``family`` will be passed to its ``Response``\ 's family.
* ``family`` is used for ``handler`` and ``callback``

  * You can use decorator ``@register()`` to add a ``handler`` to crawler. If a ``handler``\ 's family is in a ``task``\ 's families, then ``handler`` matches ``task``. It will start work on this ``task``.
  * You can use decorator ``@callback(family='')`` to add a callback to ``response``. If ``family`` in ``@callback()`` is in a ``response``\ 's families, then callback will be combined to this ``response``.

