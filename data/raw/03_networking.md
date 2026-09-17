# Computer Networks — Study Notes

## Layered Models

The OSI model has seven layers: physical, data link, network, transport, session,
presentation and application. The TCP/IP model in actual use collapses these into
four: link, internet, transport and application. Layering matters because each
layer depends only on the service offered by the layer below, so IP can run over
Ethernet or Wi-Fi without the transport layer knowing or caring.

Encapsulation is the mechanism: each layer wraps the data from the layer above in
its own header. A single HTTP request travels as an HTTP message inside a TCP
segment inside an IP packet inside an Ethernet frame.

## TCP versus UDP

TCP is connection-oriented and reliable. It establishes a connection with a
three-way handshake: the client sends SYN, the server replies SYN-ACK, the client
answers ACK. It numbers every byte, retransmits anything unacknowledged, and
delivers data to the application in order. It also performs flow control and
congestion control.

UDP is connectionless and unreliable. It adds almost nothing to IP beyond port
numbers and a checksum. There is no handshake, no retransmission and no ordering
guarantee, which makes it the right choice when late data is worse than missing
data — live video, voice calls, DNS queries and online games.

Flow control and congestion control solve different problems and are often
confused. Flow control stops a fast sender from overwhelming a slow receiver, and
is implemented with the receive window advertised in every TCP acknowledgement.
Congestion control stops senders from overwhelming the network itself, and is
implemented with the congestion window, which grows exponentially during slow
start and then linearly during congestion avoidance, halving on packet loss.

## IP Addressing and Subnetting

An IPv4 address is 32 bits, written as four dotted decimal octets. A subnet mask
splits it into a network portion and a host portion. In CIDR notation, /24 means
the first 24 bits are the network, leaving 8 bits for hosts, which gives 256
addresses of which 254 are assignable — the all-zeros address identifies the
network and the all-ones address is the broadcast address.

Private address ranges, defined in RFC 1918, are 10.0.0.0/8, 172.16.0.0/12 and
192.168.0.0/16. These are not routable on the public internet, which is why
Network Address Translation exists: a NAT router rewrites private source
addresses to its single public address and keeps a translation table to map
replies back.

IPv6 uses 128-bit addresses written as eight groups of hexadecimal digits,
removing the address exhaustion that made NAT necessary.

## DNS

DNS resolves human-readable names to IP addresses. Resolution is hierarchical: a
recursive resolver queries a root server, which refers it to the top-level domain
server for .com, which refers it to the authoritative name server for the domain,
which returns the record. Resolvers cache responses for the duration of the
record's TTL, which is why DNS changes appear to propagate slowly.

Common record types: A maps a name to an IPv4 address, AAAA to an IPv6 address,
CNAME aliases one name to another, MX designates a mail server, and TXT holds
arbitrary text used for verification records such as SPF.

## HTTP

HTTP is a stateless request-response protocol. Statelessness means the server
keeps no memory of previous requests, which is why cookies and tokens exist to
carry session identity.

Status codes are grouped by first digit: 2xx success, 3xx redirection, 4xx client
error, 5xx server error. 401 Unauthorized means authentication is missing or
invalid, while 403 Forbidden means the request was authenticated but the caller
lacks permission. 404 means the resource does not exist. 422 Unprocessable Entity
means the request was well-formed but failed validation, which is what FastAPI
returns when a Pydantic model rejects the body.

HTTPS is HTTP carried over TLS. The TLS handshake authenticates the server with a
certificate signed by a trusted certificate authority and negotiates a symmetric
session key, so the expensive asymmetric cryptography is used only for the
handshake and the bulk transfer uses fast symmetric encryption.
