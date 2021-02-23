=============
serialize_pdf
=============


.. image:: https://img.shields.io/pypi/v/serialize_pdf.svg
        :target: https://pypi.python.org/pypi/serialize_pdf

.. image:: https://img.shields.io/travis/crazycloud/serialize_pdf.svg
        :target: https://travis-ci.com/crazycloud/serialize_pdf

.. image:: https://readthedocs.org/projects/serialize-pdf/badge/?version=latest
        :target: https://serialize-pdf.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Convert pdf documents into json object. It provides additional methods for searching within the document using regex and returns the found text with bounding box information

from serialize_pdf import serialize_pdf
pdf = serialize_pdf.serialize('document.pdf')

# find value regular expression in the document
kvs = pdf.get_kv(key='Net sales',val_regex = 'Net sales.{1,20}[0-9,]*')

#







* Free software: MIT license
* Documentation: https://serialize-pdf.readthedocs.io.


Features
--------

* TODO

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.
PDF Serialize - https://github.com/JoshData/pdf-diff

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
