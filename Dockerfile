# Build the application in a build environment using the .NET SDK
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build-env

# Set the working directory in the container
WORKDIR /src

# Copy the solution file and project files
COPY OpenUtau.sln ./
COPY OpenUtau/*.csproj ./OpenUtau/
COPY OpenUtau.Core/*.csproj ./OpenUtau.Core/
COPY OpenUtau.Plugin.Builtin/*.csproj ./OpenUtau.Plugin.Builtin/
COPY OpenUtau.Test/*.csproj ./OpenUtau.Test/

# Restore dependencies
RUN dotnet restore

# Copy the rest of the source code
COPY . ./

# Build the application
RUN dotnet publish OpenUtau/OpenUtau.csproj -c Release -o /app/publish

# Build the runtime image using the Lambda .NET 7 runtime
FROM public.ecr.aws/lambda/dotnet:7

# Set the working directory for Lambda
WORKDIR /var/task

# Copy the built application from the build environment
COPY --from=build-env /app/publish ./

# Set the entry point for the Lambda container
CMD ["OpenUtau::OpenUtauCLI.Program::Main"]
