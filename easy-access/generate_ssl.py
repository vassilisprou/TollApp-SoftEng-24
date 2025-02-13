import ssl

# Generate a self-signed certificate
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

print("✅ Self-signed SSL certificate created: cert.pem, key.pem")
