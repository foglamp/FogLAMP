.. Images
.. |http_1| image:: images/http_1.jpg

.. Links
.. |http-c| raw:: html

   <a href="../foglamp-north-http-c/index.html">C++ version</a>

.. |http-python| raw:: html

   <a href="../foglamp-north-http/index.html">Python version</a>

.. |CertificateStore| raw:: html

   <a href="../../securing_FogLAMP.html#certificate-store">Certificate Store</a>

South HTTP
==========

The *foglamp-south-http* plugin allows data to be received from another FogLAMP instance. The FogLAMP which is sending the data the corresponding north task wit the HTTP north plugin installed. There are two options for the HTTP north |http-c| or |http-python|. The plugin supports both HTTP and HTTPS transport protocols and sends a JSON payload of reading data in the internal FogLAMP format.

To create a south service you, as with any other south plugin

  - Select *South* from the left hand menu bar.

  - Click on the + icon in the top left

  - Choose http_south from the plugin selection list

  - Name your service

  - Click on *Next*

  - Configure the plugin

    +----------+
    | |http_1| |
    +----------+

    - **Host**: The host name or IP address to bind to. This may be left as default, in which case the plugin binds to any address. If you have a machine with multiple network interfaces you may use this parameter to select one of those interfaces to use.

    - **Port**: The port to listen for connection from another FogLAMP instance.

    - **URL**: The URI that the plugin accepts data on. This should normally be left to the default.

    - **Asset Name Prefix**: A prefix to add to the incoming asset names. This may be left blank if you wish to preserve the same asset names.

    - **Enable HTTP**: This toggle specifies if HTTP connections should be accepted or not. If the toggle is off then only HTTPS connections can be used.

    - **Certificate Name**: The name of the certificate to use for the HTTPS encryption. This should be the name of a certificate that is stored in the FogLAMP |CertificateStore|.

  - Click *Next*

  - Enable your service and click *Done*
