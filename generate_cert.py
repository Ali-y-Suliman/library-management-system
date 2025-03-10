from OpenSSL import crypto
import os

os.makedirs('app/ssl', exist_ok=True)

k = crypto.PKey()
k.generate_key(crypto.TYPE_RSA, 2048)

cert = crypto.X509()
cert.get_subject().C = "US"
cert.get_subject().ST = "State"
cert.get_subject().L = "City"
cert.get_subject().O = "Organization"
cert.get_subject().OU = "Organizational Unit"
cert.get_subject().CN = "localhost"
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(365*24*60*60)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(k)
cert.sign(k, 'sha256')

with open('app/ssl/cert.pem', 'wb') as cert_file:
    cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

with open('app/ssl/key.pem', 'wb') as key_file:
    key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

print("SSL certificate and key generated in the 'ssl' directory")
