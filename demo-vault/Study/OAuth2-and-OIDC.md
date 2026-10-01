# OAuth 2.0 and OpenID Connect

Course notes.

## The distinction that matters

OAuth 2.0 is **authorization** - it gets an application permission to act on a resource. OpenID
Connect is a layer on top that provides **authentication** - proving who the user is - via an ID
token. Using an OAuth access token as proof of identity is a well-known mistake: it says the bearer
was granted access, not who they are.

## Roles

Resource owner (the user), client (the application), authorization server (issues tokens), resource
server (accepts them).

## Flows

- **Authorization code with PKCE** - the current recommendation for essentially every interactive
  client, including single-page and mobile applications. The code comes back through the browser and
  is exchanged for a token server to server; PKCE binds the exchange to the client that started it so
  an intercepted code is useless.
- **Client credentials** - machine to machine, no user involved.
- **Implicit** and **resource owner password credentials** - both legacy and both discouraged. Implicit
  returned tokens in the URL fragment; password credentials require the application to handle the
  user's password, which defeats much of the point.

## Tokens

- **Access token** - presented to the resource server. Short lived. May be opaque or a JWT.
- **Refresh token** - obtains new access tokens without re-authenticating. Long lived, therefore the
  valuable one to steal, therefore stored server side where possible and rotated on use.
- **ID token** - a JWT about the authentication event, for the client, never sent to a resource
  server as authorization.

## Validation

A JWT that parses is not a JWT that is valid. Verify the signature against the issuer's published
keys, the issuer, the audience, and the expiry - and reject "none" as an algorithm. Scope tells you
what was granted; it is not a role, and mapping scopes onto authorization decisions in the
application is where the actual access control lives.
